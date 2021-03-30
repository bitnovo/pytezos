from typing import Dict
from attr import dataclass


@dataclass(kw_only=True)
class MintObjkt:
    address: str
    amount: int
    metadata: str
    royalties: int


@dataclass(kw_only=True)
class Mint:
    address: str
    amount: int
    token_id: int
    token_info: Dict[str, str]
