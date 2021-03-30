

import asyncio
from collections import namedtuple
import logging
from typing import Dict, List
from pyee import AsyncIOEventEmitter
from pytezos_dapps.config import HandlerConfig, HandlerOperationConfig

from pytezos_dapps.models import OperationData
from copy import copy

class OperationCache(AsyncIOEventEmitter):
    key = namedtuple('key', ('hash', 'counter'))

    def __init__(self, handlers: List[HandlerConfig]) -> None:
        super().__init__()
        self._handlers = handlers
        self._logger = logging.getLogger(__name__)
        self._stopped = False
        self._operations: Dict[self.key, List[OperationData]] = {}

    async def add(self, operation: OperationData):
        self._logger.info('Adding operation %s to cache (%s, %s)', operation.id, operation.hash, operation.counter)
        key = (operation.hash, operation.counter)
        if key not in self._operations:
            self._operations[key] = []
        self._operations[key].append(operation)

    @classmethod
    def match_handler(cls, handler_operation: HandlerOperationConfig, operation: OperationData) -> bool:
        if handler_operation.entrypoint != operation.entrypoint:
            return False
        if handler_operation.sender and handler_operation.sender != operation.sender_address:
            return False
        if handler_operation.destination and handler_operation.destination != operation.target_address:
            return False
        if handler_operation.source and handler_operation.source != operation.initiator_address:
            return False
        return True

    async def check(self, hash, counter) -> None:
        self._logger.debug('Checking operation group (%s, %s)', hash, counter)
        key = (hash, counter)
        for handler in self._handlers:
            matched_operations = []
            for handler_operation in handler.operations:
                for operation in self._operations[key]:
                    handler_matched = self.match_handler(handler_operation, operation)
                    if handler_matched:
                        matched_operations.append(operation)

            if len(matched_operations) == len(handler.operations):
                self._logger.info('Handler `%s` matched! %s', handler.handler, key)
                self.emit('match', handler, matched_operations)
                del self._operations[key]

    async def run(self):
        while not self._stopped:
            self._logger.info('Checking %s operation groups in cache', len(self._operations))
            for hash, counter in copy(self._operations):
                await self.check(hash, counter)
            await asyncio.sleep(1)

    async def stop(self):
        self._stopped = True
