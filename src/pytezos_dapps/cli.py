import asyncio
import importlib
import logging
import os
from functools import wraps
from os.path import dirname, join

import click
from tortoise import Tortoise

from pytezos_dapps import __version__
from pytezos_dapps.config import LoggingConfig, PytezosDappConfig
from pytezos_dapps.datasources.tzkt.datasource import TzktDatasource
from pytezos_dapps.models import State

_logger = logging.getLogger(__name__)


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
@click.option('--config', '-c', type=str, help='Path to the dapp YAML config', default='config.yml')
@click.option('--logging-config', '-l', type=str, help='Path to the logging YAML config', default='logging.yml')
@click.pass_context
@click_async
async def run(_ctx, config: str, logging_config: str) -> None:
    try:
        path = join(os.getcwd(), logging_config)
        LoggingConfig.load(path).apply()
    except FileNotFoundError:
        path = join(dirname(__file__), 'configs', logging_config)
        LoggingConfig.load(path).apply()

    _logger.info('Loading config')
    try:
        path = join(os.getcwd(), config)
        _config = PytezosDappConfig.load(path)
    except FileNotFoundError:
        path = join(dirname(__file__), 'configs', config)
        _config = PytezosDappConfig.load(path)

    _config.initialize()

    try:
        _logger.info('Initializing database')
        await Tortoise.init(
            db_url=_config.database.connection_string,
            modules={
                'models': [f'{_config.package}.models'],
                'int_models': ['pytezos_dapps.models'],
            },
        )
        await Tortoise.generate_schemas()

        _logger.info('Fetching indexer state for dapp `%s`', _config.package)

        state, _ = await State.get_or_create(dapp=_config.package)

        _logger.info('Creating datasource')
        datasource_config = list(_config.datasources.values())[0].tzkt
        index_config = list(_config.indexes.values())[0].operation
        datasource = TzktDatasource(datasource_config.url, index_config, state)

        _logger.info('Starting datasource')
        await datasource.start()

    finally:
        await Tortoise.close_connections()


async def init():
    ...


async def purge():
    ...
