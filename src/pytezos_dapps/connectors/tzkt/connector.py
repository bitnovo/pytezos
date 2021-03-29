import asyncio
from functools import partial
import logging
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from cattrs_extras.converter import Converter
from signalrcore.hub.base_hub_connection import BaseHubConnection
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.transport.websockets.connection import ConnectionState

from pytezos_dapps.connectors.abstract import EventsConnector
from pytezos_dapps.models import OperationModel


class TzktEventsConnector(EventsConnector):
    def __init__(
        self,
        url: str,
        contract: str,
    ):
        self._url = url
        self._logger = logging.getLogger(__name__)
        self._subscriptions: Dict[str, List[str]] = {}
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        self._client: Optional[BaseHubConnection] = None
        self._operation_subscriptions = 0

    def _get_client(self) -> BaseHubConnection:
        if self._client is None:
            self._client = (
                HubConnectionBuilder()
                .with_url(self._url + '/v1/events')
                .configure_logging(logging.DEBUG)
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
        await self._get_client().start()

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
        self._operation_subscriptions += 1

    async def fetch_operations(self, address: str, types: List[str]) -> None:

        offset = 0
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=f'{self._url}/v1/accounts/{address}/operations',
                    params=dict(
                        type='transaction',
                        offset=offset,
                    ),
                ) as resp:
                    operations = await resp.json()

            logging.info(operations)

            await self.on_operation_message(
                address=address,
                message={'type': 1, 'data': operations},
            )

            if len(operations) < 100:
                break

            offset += 100
            print(operations[0])
            print(offset)
            await asyncio.sleep(1)

    async def on_operation_message(self, message: List[Dict[str, Any]], address: str) -> None:
        print(message)
        for item in message:
            if item['type'] != 1:
                continue
            for operation_json in item['data']:

                operation = self.convert_operation(operation_json)

                if operation.type != 'transaction':
                    continue
                if operation.parameters_json is None:
                    continue

                key = operation.entrypoint
                self._logger.debug('%s, %s', address, operation.entrypoint)
                if key in self._handlers.get(address, {}):
                    handler = self._handlers[key]
                    await handler(operation)

    async def set_handler(self, address: str, entrypoint: str, callback) -> None:
        if address not in self._subscriptions:
            self._subscriptions[address] = ['transaction']
        if address not in self._handlers:
            self._handlers[address] = {}
        if entrypoint in self._handlers[address]:
            self._logger.warning('Overriding existing handler for entrypoint `%s`', entrypoint)
        self._handlers[address][entrypoint] = callback

    @classmethod
    def convert_operation(cls, operation_json: Dict[str, Any]) -> OperationModel:
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
        return Converter().structure(operation_json, OperationModel)
