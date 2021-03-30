import asyncio
from functools import partial
import logging
from typing import Any, Callable, Dict, List, Optional, Type

import aiohttp
from cattrs_extras.converter import Converter
from pytezos_dapps.config import HandlerConfig
from pytezos_dapps.connectors.tzkt.cache import OperationCache
from signalrcore.hub.base_hub_connection import BaseHubConnection
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.transport.websockets.connection import ConnectionState

from pytezos_dapps.connectors.tzkt.enums import TzktMessageType
from pytezos_dapps.connectors.abstract import EventsConnector
from pytezos_dapps.models import HandlerContext, OperationData, Transaction


class TzktEventsConnector(EventsConnector):
    def __init__(self, url: str, handlers: List[HandlerConfig]):
        super().__init__()
        self._url = url
        self._handlers = handlers
        self._logger = logging.getLogger(__name__)
        self._subscriptions: Dict[str, List[str]] = {}
        self._client: Optional[BaseHubConnection] = None
        self._checkpoint = None
        self._cache = OperationCache(handlers)
        self._cache.on('match', self.on_match)

    @property
    def checkpoint(self):
        return self._checkpoint

    @checkpoint.setter
    def checkpoint(self, value: str):
        if self._client:
            raise Exception('Checkpoint must be set before starting websocket client')
        self._checkpoint = value

    def _get_client(self) -> BaseHubConnection:
        if self._client is None:
            self._client = (
                HubConnectionBuilder()
                .with_url(self._url + '/v1/events')
                .with_automatic_reconnect(
                    {
                        "type": "raw",
                        "keep_alive_interval": 10,
                        "reconnect_interval": 5,
                        "max_attempts": 5,
                    }
                )
            ).build()
            self._client.on_open(self.on_connect)

        return self._client

    async def start(self):
        for handler in self._handlers:
            await self.add_subscription(handler.contract)

        await asyncio.gather(
            self._cache.run(),
            self._get_client().start(),
        )

    async def stop(self):
        ...

    async def on_connect(self):
        for address, subscriptions in self._subscriptions.items():
            await self.subscribe_to_operations(address, subscriptions)

    async def subscribe_to_operations(self, address: str, types: List[str]) -> None:
        self._get_client().on(
            'operations',
            partial(self.on_operation_message, address=address),
        )

        while self._get_client().transport.state != ConnectionState.connected:
            await asyncio.sleep(0.1)

        await self._get_client().send(
            'SubscribeToOperations',
            [
                {
                    'address': address,
                    'types': ','.join(types),
                }
            ],
        )

    async def fetch_operations(self) -> None:
        for address in self._subscriptions:
            limit = 1000
            offset = 0
            while True:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url=f'{self._url}/v1/operations/transactions',
                        params={
                            "anyof.sender.target.initiator": address,
                            "offset": offset,
                            "limit": limit,
                        },
                    ) as resp:
                        operations = await resp.json()

                logging.info(operations)

                await self.on_operation_message(
                    address=address,
                    message=[
                        {
                            'type': TzktMessageType.DATA.value,
                            'data': operations,
                        },
                    ],
                )

                if len(operations) < limit:
                    break

                offset += limit
                await asyncio.sleep(1)


    async def on_operation_message(self, message: List[Dict[str, Any]], address: str) -> None:
        for item in message:
            message_type = TzktMessageType(item['type'])
            if message_type != TzktMessageType.DATA:
                continue
            for operation_json in item['data']:

                operation = self.convert_operation(operation_json)

                if operation.type != 'transaction':
                    continue

                await self._cache.add(operation)

    async def add_subscription(self, address: str, types: Optional[List[str]] = None) -> None:
        if types is None:
            types = ['transaction']
        if address not in self._subscriptions:
            self._subscriptions[address] = types

    async def on_match(self, handler_config: HandlerConfig, operations: List[OperationData]):
        handler = handler_config.handler_callable
        args = []
        for handler_operation, operation in zip(handler_config.operations, operations):
            transaction, _ = await Transaction.get_or_create(id=operation.id, block=operation.block)

            parameters_type = handler_operation.parameters_type
            parameters = Converter().structure(operation.parameters_json, parameters_type)

            context = HandlerContext[parameters_type](
                data=operation,
                transaction=transaction,
                parameters=parameters,
            )
            args.append(context)

        await handler(*args)


    @classmethod
    def convert_operation(cls, operation_json: Dict[str, Any]) -> OperationData:
        operation_json['initiator_address'] = operation_json.get('initiator', {}).get('address')
        operation_json['sender_address'] = operation_json['sender']['address']
        operation_json['sender_alias'] = operation_json['sender'].get('alias')
        operation_json['gas_limit'] = operation_json['gasLimit']
        operation_json['gas_used'] = operation_json['gasUsed']
        operation_json['storage_limit'] = operation_json['storageLimit']
        operation_json['storage_used'] = operation_json['storageUsed']
        operation_json['baker_fee'] = operation_json['bakerFee']
        operation_json['storage_fee'] = operation_json['storageFee']
        operation_json['allocation_fee'] = operation_json['allocationFee']
        operation_json['target_alias'] = operation_json['target'].get('alias')
        operation_json['target_address'] = operation_json['target']['address']
        operation_json['entrypoint'] = operation_json.get('parameter', {}).get('entrypoint')
        operation_json['parameters_json'] = operation_json.get('parameter', {}).get('value')
        operation_json['has_internals'] = operation_json['hasInternals']
        return Converter().structure(operation_json, OperationData)
