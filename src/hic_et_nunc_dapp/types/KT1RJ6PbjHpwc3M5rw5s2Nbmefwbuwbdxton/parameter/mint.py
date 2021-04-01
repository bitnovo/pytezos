# generated by datamodel-codegen:
#   filename:  mint.json
#   timestamp: 2021-04-01T05:48:09+00:00

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Extra


class TokenInfo(BaseModel):
    class Config:
        extra = Extra.allow

    __root__: str


class Mint(BaseModel):
    address: str
    amount: str
    token_id: str
    token_info: Dict[str, TokenInfo]
