import os
from typing import Any, Dict, List, Optional, Type, Union

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
class HandlerConfig:
    contract: str
    entrypoint: str
    handler: str


@dataclass(kw_only=True)
class PytezosDappConfig:
    tzkt: TzktConfig
    database: Union[SqliteDatabaseConfig, DatabaseConfig] = SqliteDatabaseConfig()
    contracts: Dict[str, str]
    handlers: List[HandlerConfig]
    debug: bool = False

    @classmethod
    def load(
        cls,
        filename: str,
        cls_override: Optional[Type] = None,
        converter_override: Optional[Converter] = None,
    ) -> 'PytezosDappConfig':

        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)
        converter = Converter() or converter_override

        with open(filename) as file:
            raw_config = YAML(typ='base').load(file.read())
        config = converter.structure(raw_config, cls_override or cls)
        return config
