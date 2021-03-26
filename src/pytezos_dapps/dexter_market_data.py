from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector
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


async def run():

    await Tortoise.init(
        db_url='sqlite:///home/droserasprout/git/pytezos/db.sqlite3',
        modules={'models': ['pytezos_dapps.dapps.hic_et_nunc.models']}
    )
    with suppress(Exception):
        await Tortoise.generate_schemas()

    connector = TzktEventsConnector(url)
    await connector.start()

    await asyncio.gather(
        # monitor(connector),
        connector.subscribe_to_operations(address, ['transaction']),
        # connector.fetch_operations(address, ['transaction']),
        # monitor(connector)
    )

    while True:
        await asyncio.sleep(1)

    await Tortoise.close_connections()
