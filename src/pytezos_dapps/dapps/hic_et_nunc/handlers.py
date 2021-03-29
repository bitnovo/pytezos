from gettext import translation
import logging

from pytezos_dapps.dapps.hic_et_nunc.models import Address, Token
from pytezos_dapps.models import HandlerContext, OperationData

logger = logging.getLogger(__name__)


async def on_mint(ctx: HandlerContext):
    print('on_mint', ctx.data.parameters_json)
    address = await Address.filter(address=ctx.data.parameters_json['address']).get_or_none()
    if address is None:
        address = Address(address=ctx.data.parameters_json['address'])
        await address.save()

    for _ in ctx.data.parameters_json['amount']:
        token = Token(
            token_id=ctx.data.parameters_json['token_id'],
            token_info=ctx.data.parameters_json['token_info'][''],
            holder=address,
            transaction=ctx.transaction,
        )
        await token.save()


async def on_transfer(ctx: HandlerContext):
    print('STUB', 'on_transfer', ctx.data.parameters_json)


async def on_curate(ctx: HandlerContext):
    print('STUB', 'on_curate', ctx.data.parameters_json)


async def on_collect(ctx: HandlerContext):
    print('STUB', 'on_collect', ctx.data.parameters_json)
