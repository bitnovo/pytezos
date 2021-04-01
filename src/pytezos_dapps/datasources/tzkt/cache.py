from copy import copy
import logging
from collections import namedtuple
from typing import Awaitable, Callable, Dict, List
from pytezos_dapps.config import OperationHandlerPatternConfig, OperationIndexConfig

from pytezos_dapps.models import OperationData

OperationGroup = namedtuple('OperationGroup', ('hash', 'counter'))


class OperationCache:
    def __init__(self, index_config: OperationIndexConfig, level: int) -> None:
        super().__init__()
        self._index_config = index_config
        self._level = level
        self._logger = logging.getLogger(__name__)
        self._stopped = False
        self._operations: Dict[OperationGroup, List[OperationData]] = {}
        self._previous_operations: Dict[OperationGroup, List[OperationData]] = {}

    async def add(self, operation: OperationData):
        self._logger.debug('Adding operation %s to cache (%s, %s)', operation.id, operation.hash, operation.counter)
        key = OperationGroup(operation.hash, operation.counter)
        self._level = max(operation.level, self._level)
        if key not in self._operations:
            self._operations[key] = []
        self._operations[key].append(operation)

    def match_operation(self, pattern_config: OperationHandlerPatternConfig, operation: OperationData) -> bool:
        self._logger.debug('pattern: %s, %s', pattern_config.entrypoint, pattern_config.destination)
        self._logger.debug('operation: %s, %s', operation.entrypoint, operation.target_address)
        if pattern_config.entrypoint != operation.entrypoint:
            return False
        if pattern_config.sender and pattern_config.sender != operation.sender_address:
            return False
        if pattern_config.source and pattern_config.source != operation.initiator_address:
            return False
        if pattern_config.destination and pattern_config.destination != operation.target_address:
            return False
        self._logger.debug('Match!')
        return True

    async def process(
        self,
        callback: Callable[[OperationIndexConfig, List[OperationData]], Awaitable[None]],
    ) -> int:
        keys = list(self._operations.keys())
        self._logger.info('Matching %s operation groups', len(keys))
        for key, operations in copy(self._operations).items():
            self._logger.debug('Processing %s', key)
            for handler_config in self._index_config.handlers:
                matched_operations = []
                for pattern_config in handler_config.pattern:
                    for operation in operations:
                        operation_matched = self.match_operation(pattern_config, operation)
                        if operation_matched:
                            matched_operations.append(operation)

                if len(matched_operations) == len(handler_config.pattern):
                    self._logger.info('Handler `%s` matched! %s', handler_config.callback, key)
                    await callback(handler_config, matched_operations)
                    if key in self._operations:
                        del self._operations[key]

        keys_left = self._operations.keys()
        self._logger.info('%s operation groups unmatched', len(keys_left))
        self._logger.info('Current level: %s', self._level)
        self._operations = {}
        return self._level

    async def stop(self):
        self._stopped = True
