import os
from typing import Dict, Optional, Type

from attr import dataclass
from cattr import Converter
from ruamel.yaml import YAML


@dataclass(kw_only=True)
class DatabaseConfig:
    connection_string: str

@dataclass(kw_only=True)
class TzktConfig:
    url: str


@dataclass(kw_only=True)
class PytezosDappConfig:
    tzkt: TzktConfig
    database: DatabaseConfig
    contract: str
    handlers: Dict[str, str]
    module: str

    @classmethod
    def load(
        cls: Type['Config'],
        filename: str,
        cls_override: Optional[Type] = None,
        converter_override: Optional[Converter] = None,
    ) -> 'Config':

        current_workdir = os.path.join(os.getcwd())
        filename = os.path.join(current_workdir, filename)
        converter = Converter() or config_converter

        with open(filename) as file:
            raw_config = YAML(typ='base').load(file.read())
        config = converter.structure(raw_config, cls_override or cls)
        return config
