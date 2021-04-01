# generated by datamodel-codegen:
#   filename:  hDAO_batch.json

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class HDAOBatchItem(BaseModel):
    amount: str
    to_: str


class HDAOBatch(BaseModel):
    __root__: List[HDAOBatchItem]
