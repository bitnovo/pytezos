from pytezos_indexer.connectors.tzkt.connector import TzktEventsConnector
from time import sleep
import logging
from tortoise import Tortoise
from contextlib import suppress
import asyncio
logging.basicConfig()
logging.getLogger().setLevel(0)
url = 'https://api.tzkt.io'
# address = 'KT1AbYeDbjjcAnV1QK7EZUUdqku77CdkTuv6'
address = 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9'

async def monitor(connector):
    while True:
        count = await connector.count_transactions()
        logging.info(f'{count} transactions in database')
        await asyncio.sleep(1)


async def run():

    await Tortoise.init(
        db_url='sqlite:///home/droserasprout/git/pytezos/db.sqlite3',
        modules={'models': ['pytezos_indexer.connectors.tzkt.models']}
    )
    with suppress(Exception):
        await Tortoise.generate_schemas()

    connector = TzktEventsConnector(url)
    await connector.start()

    await asyncio.gather(
        monitor(connector),
        connector.subscribe_to_operations(address, ['transaction']),
        # connector.fetch_operations(address, ['transaction']),
        # monitor(connector)
    )

    await Tortoise.close_connections()

# 2021-03-26 10:43:22,235 - SignalRCoreClient - DEBUG - Sending message InvocationMessage: invocation_id 30e8fc96-6883-4308-ae8a-c93d88204506, target SubscribeToOperations, arguments [{'address': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9', 'types': 'transaction'}]
# DEBUG:SignalRCoreClient:Sending message InvocationMessage: invocation_id 30e8fc96-6883-4308-ae8a-c93d88204506, target SubscribeToOperations, arguments [{'address': 'KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9', 'types': 'transaction'}]
# 2021-03-26 10:43:22,235 - SignalRCoreClient - DEBUG - {"type": 1, "headers": {}, "target": "SubscribeToOperations", "arguments": [{"address": "KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9", "types": "transaction"}], "invocationId": "30e8fc96-6883-4308-ae8a-c93d88204506"}
# DEBUG:SignalRCoreClient:{"type": 1, "headers": {}, "target": "SubscribeToOperations", "arguments": [{"address": "KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9", "types": "transaction"}], "invocationId": "30e8fc96-6883-4308-ae8a-c93d88204506"}
# DEBUG:db_client:SELECT COUNT(*) FROM "transaction": None
# DEBUG:aiosqlite:executing functools.partial(<bound method Connection._execute_fetchall of <Connection(Thread-1, started 140345491850816)>>, 'SELECT COUNT(*) FROM "transaction"', [])
# DEBUG:aiosqlite:operation functools.partial(<bound method Connection._execute_fetchall of <Connection(Thread-1, started 140345491850816)>>, 'SELECT COUNT(*) FROM "transaction"', []) completed
# INFO:root:160 transactions in database
# 2021-03-26 10:43:22,291 - SignalRCoreClient - DEBUG - Message received{"type":1,"target":"operations","arguments":[{"type":0,"state":1401206}]}{"type":3,"invocationId":"30e8fc96-6883-4308-ae8a-c93d88204506","result":null}
# DEBUG:SignalRCoreClient:Message received{"type":1,"target":"operations","arguments":[{"type":0,"state":1401206}]}{"type":3,"invocationId":"30e8fc96-6883-4308-ae8a-c93d88204506","result":null}
# 2021-03-26 10:43:22,292 - SignalRCoreClient - DEBUG - Raw message incomming: 
# DEBUG:SignalRCoreClient:Raw message incomming: 
