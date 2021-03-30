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
from pytezos_dapps.config import PytezosDappConfig, LoggingConfig
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
@click.option('--logging-config', '-l', type=str, help='Path to the logging YAML config', default='logging.yml')
@click.pass_context
@click_async
async def run(_ctx, dapp: str, config: str, logging_config: str) -> None:
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

    _logger.info('Setting up handlers and parameters')
    handlers = importlib.import_module(f'pytezos_dapps.dapps.{dapp}.handlers')
    parameters = importlib.import_module(f'pytezos_dapps.dapps.{dapp}.parameters')

    for handler_config in _config.handlers:
        _logger.info('Registering handler `%s`', handler_config.handler)
        handler = getattr(handlers, handler_config.handler)
        handler_config.handler_callable = handler

        for handler_operation in handler_config.operations:
            _logger.info('Registering parameters type `%s`', handler_operation.parameters)
            parameters_type = getattr(parameters, handler_operation.parameters)
            handler_operation.parameters_type = parameters_type

    _logger.info('Creating connector')
    connector = TzktEventsConnector(_config.tzkt.url, _config.handlers)

    try:
        _logger.info('Initializing database')
        await Tortoise.init(
            db_url=_config.database.connection_string,
            modules={
                'models': [f'pytezos_dapps.dapps.{dapp}.models'],
                'int_models': ['pytezos_dapps.models']
            },
        )
        await Tortoise.generate_schemas()

        _logger.info('Starting connector')
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