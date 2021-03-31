import hashlib
import importlib
import json
import logging.config
import os
from typing import Any, Callable, Dict, List, Optional, Type, Union

from attr import dataclass
from cattrs_extras.converter import Converter
from ruamel.yaml import YAML


@dataclass(kw_only=True)
class SqliteDatabaseConfig:
    path: str = ':memory:'

    @property
    def connection_string(self):
        return f'sqlite://{self.path}'


@dataclass(kw_only=True)
class DatabaseConfig:
    driver: str
    host: str
    port: int
    user: str
    password: str = ''
    database: str

    @property
    def connection_string(self):
        if self.driver == 'sqlite':
            return f'{self.driver}://{self.path}'
        return f'{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'


@dataclass(kw_only=True)
class TzktConfig:
    url: str


@dataclass(kw_only=True)
class HandlerOperationConfig:
    source: Optional[str] = None
    destination: Optional[str] = None
    sender: Optional[str] = None
    entrypoint: str
    parameters: str

    def __attrs_post_init__(self):
        if not any([self.source, self.destination, self.sender]):
            raise Exception('You must specify any of source/destination/sender to match handler')
        self._parameters_type = None

    @property
    def parameters_type(self) -> Type:
        if self._parameters_type is None:
            raise Exception('Parameters type is not registered')
        return self._parameters_type

    @parameters_type.setter
    def parameters_type(self, typ: Type) -> None:
        self._parameters_type = typ


@dataclass(kw_only=True)
class HandlerConfig:
    handler: str
    contract: str
    operations: List[HandlerOperationConfig]

    def __attrs_post_init__(self):
        self._handler_callable = None

    @property
    def handler_callable(self) -> Callable:
        if self._handler_callable is None:
            raise Exception('Handler callable is not registered')
        return self._handler_callable

    @handler_callable.setter
    def handler_callable(self, fn: Callable) -> None:
        self._handler_callable = fn


@dataclass(kw_only=True)
class PytezosDappConfig:
    dapp: str
    tzkt: TzktConfig
    database: Union[SqliteDatabaseConfig, DatabaseConfig] = SqliteDatabaseConfig()
    contracts: Dict[str, str]
    handlers: List[HandlerConfig]
    debug: bool = False

    def __attrs_post_init__(self):
        self._logger = logging.getLogger(__name__)
        for handler in self.handlers:
            if handler.contract in self.contracts:
                handler.contract = self.contracts[handler.contract]
            for operation in handler.operations:
                if operation.source in self.contracts:
                    operation.source = self.contracts[operation.source]
                if operation.destination in self.contracts:
                    operation.destination = self.contracts[operation.destination]
                if operation.sender in self.contracts:
                    operation.sender = self.contracts[operation.sender]

    @classmethod
    def load(
        cls,
        filename: str,
        cls_override: Optional[Type] = None,
        converter_override: Optional[Converter] = None,
    ) -> 'PytezosDappConfig':

        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)
        converter = converter_override or Converter()

        with open(filename) as file:
            raw_config = YAML(typ='base').load(file.read())
        config = converter.structure(raw_config, cls_override or cls)
        return config

    def hash(self):
        return hashlib.sha256(json.dumps(Converter().unstructure(self)).encode()).hexdigest()[-8:]

    def initialize(self) -> None:
        self._logger.info('Setting up handlers and parameters for dapp `%s`', self.dapp)
        handlers = importlib.import_module(f'pytezos_dapps.dapps.{self.dapp}.handlers')
        parameters = importlib.import_module(f'pytezos_dapps.dapps.{self.dapp}.parameters')

        for handler_config in self.handlers:
            self._logger.info('Registering handler `%s`', handler_config.handler)
            handler = getattr(handlers, handler_config.handler)
            handler_config.handler_callable = handler

            for handler_operation in handler_config.operations:
                self._logger.info('Registering parameters type `%s`', handler_operation.parameters)
                parameters_type = getattr(parameters, handler_operation.parameters)
                handler_operation.parameters_type = parameters_type


@dataclass(kw_only=True)
class LoggingConfig:
    config: Dict[str, Any]

    @classmethod
    def load(
        cls,
        filename: str,
    ) -> 'LoggingConfig':

        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)

        with open(filename) as file:
            return cls(config=YAML().load(file.read()))

    def apply(self):
        logging.config.dictConfig(self.config)
