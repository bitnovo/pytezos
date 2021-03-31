import logging
from gettext import translation
from pytezos_dapps.dapps.hic_et_nunc.parameters.KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9.mint_OBJKT import MintObjkt
from pytezos_dapps.dapps.hic_et_nunc.parameters.KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton.mint import Mint

from pytezos_dapps.models import HandlerContext

from .models import Address, Token

logger = logging.getLogger(__name__)


async def on_mint(mint_objct: HandlerContext[MintObjkt], mint: HandlerContext[Mint]):
    address, _ = await Address.get_or_create(address=mint.parameters.address)

    for _ in range(int(mint.parameters.amount)):
        token = Token(
            token_id=int(mint.parameters.token_id),
            token_info=mint.parameters.token_info[''],
            holder=address,
            transaction=mint.transaction,
        )
        await token.save()
