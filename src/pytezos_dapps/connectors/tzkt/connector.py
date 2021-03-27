

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from signalrcore.hub.base_hub_connection import BaseHubConnection
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.transport.websockets.connection import ConnectionState

from pytezos_dapps.connectors.abstract import EventsConnector


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
                        "max_attempts": 5
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
            [{
                'address': address,
                'types': ','.join(types),
            }]
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
                    )
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
            for operation in item['data']:

                if operation['type'] != 'transaction':
                    continue
                if 'parameter' not in operation:
                    continue

                key = operation['parameter']['entrypoint']
                print('key', key)
                if key in self._handlers:
                    handler = self._handlers[key]
                    await handler(operation['parameter']['value'])

    async def set_handler(self, entrypoint: str, callback):
        self._handlers[entrypoint] = callback

    async def start(self):
        await self._get_client().start()
