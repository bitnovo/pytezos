import logging
from typing import Dict, Any
from pytezos_dapps.dapps.hic_et_nunc.models import Address, Token

logger = logging.getLogger(__name__)

async def on_mint(params: Dict[str, Any]):
    logging.warning('ON MINT')
    logging.debug(params)

    address = await Address.filter(address=params['address']).get_or_create()
    for _ in params['amount']:
        token = Token(
            token_id=params['token_id'],
            token_info=params['token_info'][''],
        )
        await token.save()

async def on_transfer(params: Dict[str, Any]):
    logging.warning('ON TRANSFER')
    logging.debug(params)

async def on_curate(params: Dict[str, Any]):
    logging.warning('ON CURATE')
    logging.debug(params)