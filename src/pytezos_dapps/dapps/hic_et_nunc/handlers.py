import logging
from gettext import translation

from pytezos_dapps.models import HandlerContext

from .models import Address, Token
from .parameters import Mint, MintObjkt

logger = logging.getLogger(__name__)


async def on_mint(mint_objct: HandlerContext[MintObjkt], mint: HandlerContext[Mint]):
    address, _ = await Address.get_or_create(address=mint.parameters.address)

    for _ in range(mint.parameters.amount):
        token = Token(
            token_id=mint.parameters.token_id,
            token_info=mint.parameters.token_info[''],
            holder=address,
            transaction=mint.transaction,
        )
        await token.save()
