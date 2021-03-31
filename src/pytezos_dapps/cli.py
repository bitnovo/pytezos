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
from pytezos_dapps.connectors.tzkt.connector import TzktEventsConnector
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
    except Exception:
        path = join(dirname(__file__), 'configs', logging_config)
        LoggingConfig.load(path).apply()

    _logger.info('Loading config')
    try:
        path = join(os.getcwd(), config)
        _config = PytezosDappConfig.load(path)
    except Exception:
        path = join(dirname(__file__), 'configs', config)
        _config = PytezosDappConfig.load(path)

    _config.initialize()

    try:
        _logger.info('Initializing database')
        await Tortoise.init(
            db_url=_config.database.connection_string,
            modules={
                'models': [f'pytezos_dapps.dapps.{_config.dapp}.models'],
                'int_models': ['pytezos_dapps.models'],
            },
        )
        await Tortoise.generate_schemas()

        config_hash = _config.hash()
        _logger.info('Fetching indexer state for config %s', config_hash)

        state, _ = await State.get_or_create(dapp=_config.dapp, defaults={'hash': config_hash})
        if state.hash != config_hash:
            raise Exception(
                f'Config has been changed (hash {config_hash}, expected {state.hash}). '
                f'Cleanup database or update `state` table before starting indexing again.'
            )

        _logger.info('Creating connector')
        connector = TzktEventsConnector(_config.tzkt.url, _config.handlers, state)

        _logger.info('Starting connector')
        await connector.start()

    finally:
        await Tortoise.close_connections()


async def init():
    ...


async def purge():
    ...
