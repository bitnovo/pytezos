import logging
from typing import Dict, Any
from pytezos_dapps.dapps.hic_et_nunc.models import Address, Token

logger = logging.getLogger(__name__)

async def on_mint(params: Dict[str, Any]):
    print('on_mint', params)
    address = await Address.filter(address=params['address']).get_or_none()
    if address is None:
        address = Address(address=params['address'])
        await address.save()

    for _ in params['amount']:
        token = Token(
            token_id=params['token_id'],
            token_info=params['token_info'][''],
            holder=address,
        )
        await token.save()

async def on_transfer(params: Dict[str, Any]):
    print('STUB', 'on_transfer', params)

async def on_curate(params: Dict[str, Any]):
    print('STUB', 'on_curate', params)

async def on_collect(params: Dict[str, Any]):
    print('STUB', 'on_collect', params)