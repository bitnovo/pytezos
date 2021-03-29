import logging
import click
from pytezos_dapps import __version__
import sys
import os
import asyncio
import importlib
from contextlib import suppress
from functools import  wraps
from tortoise import Tortoise
from os.path import join, dirname
from pytezos_dapps.config import PytezosDappConfig
from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector

_logger = logging.getLogger(__name__)

import asyncio
from functools import update_wrapper

def click_async(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))

    return wrapper


@click.group()
@click.version_option(__version__)
@click.pass_context
@click_async
async def cli(*_args, **_kwargs):
    pass


@cli.command(help='Run pytezos dapp')
@click.option('--dapp', '-d', type=str, help='Dapp name')
@click.option('--config', '-c', type=str, help='Path to the dapp YAML config', default='config.yml')
@click.pass_context
@click_async
async def run(_ctx, dapp: str, config: str) -> None:
    logging.basicConfig()

    handlers = importlib.import_module(f'pytezos_dapps.dapps.{dapp}.handlers')

    config = PytezosDappConfig.load(join(os.getcwd(), config))

    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    connector = TzktEventsConnector(config.tzkt.url)

    for handler_config in config.handlers:
        address = config.contracts[handler_config.contract]
        handler = getattr(handlers, handler_config.handler)
        await connector.set_handler(address, handler_config.entrypoint, handler)

    try:
        await Tortoise.init(
            db_url=config.database.connection_string,
            modules={
                'models': [f'pytezos_dapps.dapps.{dapp}.models'],
                'int_models': ['pytezos_dapps.models']
            },
        )
        await Tortoise.generate_schemas()

        await asyncio.gather(
            connector.start(),
            connector.fetch_operations(),
        )
    finally:
        await Tortoise.close_connections()

async def init():
    ...

async def purge():
    ...