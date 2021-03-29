import asyncio
import logging
from typing import Any, Dict, List, Optional

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
        self._contract = contract
        self._handlers = {}
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
        await self.subscribe_to_operations(self._contract, ['transaction'])

    async def subscribe_to_operations(self, address: str, types: List[str]) -> None:
        self._get_client().on('operations', self.on_operation_message)

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

            for operation in operations:
                await self.on_operation_message([operation])

            if len(operations) < 100:
                break

            offset += 100
            print(operations[0])
            print(offset)
            await asyncio.sleep(1)

    async def on_operation_message(self, message: List[Dict[str, Any]]):
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
                print('key', key)
                if key in self._handlers:
                    handler = self._handlers[key]
                    await handler(operation)

    async def set_handler(self, entrypoint: str, callback):
        self._handlers[entrypoint] = callback

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
