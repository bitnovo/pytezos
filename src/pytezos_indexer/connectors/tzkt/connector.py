

from pytezos_indexer.connectors.abstract import EventsConnector
from pytezos_indexer.connectors.tzkt.models import Transaction
from tortoise.exceptions import OperationalError

from signalrcore_async.hub_connection_builder import HubConnectionBuilder
from signalrcore_async.hub.base_hub_connection import BaseHubConnection
from signalrcore_async.hub.connection_state import ConnectionState
# from signalrcore.hub_connection_builder import HubConnectionBuilder
# from signalrcore.hub.base_hub_connection import BaseHubConnection


import aiohttp
import asyncio
from typing import List, Dict, Any
from contextlib import suppress
import logging

class TzktEventsConnector(EventsConnector):
    def __init__(
        self,
        url: str,
    ):
        self._url = url
        self._client: Optional[BaseHubConnection] = None
        self._operation_subscriptions = 0

    def _get_client(self) -> BaseHubConnection:
        if self._client is None:
            self._client = hub_connection = (
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

        return self._client

    async def start(self):
        await self._get_client().start()

    async def stop(self):
        ...

    async def subscribe_to_operations(self, address: str, types: List[str]) -> None:
        self._get_client().on('operations', self.on_transaction)

        while self._get_client().state != ConnectionState.connected:
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
                await self.on_transaction([operation])

            if len(operations) < 100:
                break

            offset += 100
            print(operations[0])
            print(offset)
            await asyncio.sleep(1)

    async def on_transaction(self, message: List[Dict[str, Any]]):
        print(message)
        for item in message:
            if item['type'] != 1:
                continue
            for transaction in item['data']:
                transaction_model = Transaction.from_json(transaction)
                with suppress(OperationalError):
                    await transaction_model.save()

    async def count_transactions(self) -> int:
        return await Transaction.filter().count()

    async def start(self):
        await self._get_client().start()
