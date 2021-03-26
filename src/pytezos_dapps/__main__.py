import asyncio

from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector
from pytezos_dapps.dapps.hic_et_nunc.handlers import on_mint, on_transfer, on_curate, on_collect
from pytezos_dapps.config import PytezosDappConfig
from time import sleep
import logging
from tortoise import Tortoise
from contextlib import suppress
import asyncio
import importlib

logging.basicConfig()
logging.getLogger().setLevel(0)


async def run():

    config = PytezosDappConfig.load('git/pytezos/src/pytezos_dapps/config.yml')

    await Tortoise.init(
        db_url=config.database.connection_string,
        modules={'models': [config.module + '.models']}
    )
    with suppress(Exception):
        await Tortoise.generate_schemas()

    connector = TzktEventsConnector(config.tzkt.url, config.contract)

    handlers = importlib.import_module(config.module + '.handlers')
    for event, handler_name in config.handlers.items():
        handler = getattr(handlers, handler_name)
        await connector.set_handler(event, handler)

    try:
        await connector.start()
    finally:
        await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(run())