import os
from typing import Dict, List, Optional, Type

from attr import dataclass
from cattrs_extras.converter import Converter
from ruamel.yaml import YAML


@dataclass(kw_only=True)
class DatabaseConfig:
    connection_string: str


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
    database: DatabaseConfig
    contracts: Dict[str, str]
    handlers: List[HandlerConfig]
    module: str

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
