

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

    def __init__(self, handlers: List[HandlerConfig], level: int) -> None:
        super().__init__()
        self._handlers = handlers
        self._level = level
        self._logger = logging.getLogger(__name__)
        self._stopped = False
        self._operations: Dict[self.key, List[OperationData]] = {}
        self._previous_operations: Dict[self.key, List[OperationData]] = {}

    def __getitem__(self, key):
        return self._operations.get(key, []) + self._previous_operations.get(key, [])

    async def add(self, operation: OperationData):
        self._logger.debug('Adding operation %s to cache (%s, %s)', operation.id, operation.hash, operation.counter)
        key = (operation.hash, operation.counter)
        self._level = max(operation.level, self._level)
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

    async def check(self) -> int:
        keys = self._operations.keys() | self._previous_operations.keys()
        self._logger.info('Matching %s operation groups', len(keys))
        for key in keys:
            for handler in self._handlers:
                matched_operations = []
                for handler_operation in handler.operations:
                    operations = self[key]
                    for operation in operations:
                        handler_matched = self.match_handler(handler_operation, operation)
                        if handler_matched:
                            matched_operations.append(operation)

                if len(matched_operations) == len(handler.operations):
                    self._logger.info('Handler `%s` matched! %s', handler.handler, key)
                    self.emit('match', handler, matched_operations)
                    if key in self._operations:
                        del self._operations[key]
                    if key in self._previous_operations:
                        del self._previous_operations[key]

        keys_left = self._operations.keys() | self._previous_operations.keys()
        self._logger.info('%s operation groups unmatched', len(keys_left))
        self._logger.info('Current level: %s', self._level)
        return self._level


    def flush(self):
        keys = self._previous_operations.keys()
        self._logger.info('Dropping %s operation groups from previous batch', len(keys))

        self._previous_operations = self._operations
        self._operations = {}

    async def stop(self):
        self._stopped = True
