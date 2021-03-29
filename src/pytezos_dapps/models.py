from datetime import datetime
from typing import Any, Optional

from attr import dataclass


@dataclass(kw_only=True)
class OperationModel:
    type: str
    id: int
    level: int
    timestamp: datetime
    block: str
    hash: str
    counter: int
    initiator_address: Optional[str] = None
    sender_address: str
    sender_alias: Optional[str] = None
    nonce: Optional[int] = None
    gas_limit: int
    gas_used: int
    storage_limit: int
    storage_used: int
    baker_fee: int
    storage_fee: int
    allocation_fee: int
    target_alias: Optional[str] = None
    target_address: str
    amount: int
    entrypoint: Optional[str] = None
    parameters_json: Optional[Any] = None
    status: str
    has_internals: bool
    parameters: Optional[str] = None
