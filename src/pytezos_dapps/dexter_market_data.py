from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector
from pytezos_dapps.dapps.hic_et_nunc.handlers import on_mint, on_transfer, on_curate, on_collect
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

    await connector.set_handler('mint', on_mint)
    await connector.set_handler('transfer', on_transfer)
    await connector.set_handler('curate', on_curate)
    await connector.set_handler('collect', on_collect)


    await asyncio.gather(
        connector.start(),
        connector.subscribe_to_operations(address, ['transaction']),
        # connector.fetch_operations(address, ['transaction']),
        # monitor(connector)
    )

    await Tortoise.close_connections()
