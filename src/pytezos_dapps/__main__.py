import asyncio
import importlib
import logging
from contextlib import suppress
from time import sleep

from tortoise import Tortoise

from pytezos_dapps.config import PytezosDappConfig
from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector
from pytezos_dapps.dapps.hic_et_nunc.handlers import on_collect, on_curate, on_mint, on_transfer

logging.basicConfig()
logging.getLogger().setLevel(0)


async def run():

    config = PytezosDappConfig.load('git/pytezos/src/pytezos_dapps/config.yml')

    await Tortoise.init(db_url=config.database.connection_string, modules={'models': [config.module + '.models']})
    with suppress(Exception):
        await Tortoise.generate_schemas()

    connector = TzktEventsConnector(config.tzkt.url)

    handlers = importlib.import_module(config.module + '.handlers')
    for handler_config in config.handlers:
        address = config.contracts[handler_config.contract]
        handler = getattr(handlers, handler_config.handler)
        await connector.set_handler(address, handler_config.entrypoint, handler)

    try:
        await asyncio.gather(
            connector.start(),
            connector.fetch_operations(),
        )
    finally:
        await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(run())
