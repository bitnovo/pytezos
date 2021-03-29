import logging

from pytezos_dapps.dapps.hic_et_nunc.models import Address, Token
from pytezos_dapps.models import OperationModel

logger = logging.getLogger(__name__)

async def on_mint(operation: OperationModel):
    print('on_mint', operation.parameters_json)
    address = await Address.filter(address=operation.parameters_json['address']).get_or_none()
    if address is None:
        address = Address(address=operation.parameters_json['address'])
        await address.save()

    for _ in operation.parameters_json['amount']:
        token = Token(
            token_id=operation.parameters_json['token_id'],
            token_info=operation.parameters_json['token_info'][''],
            holder=address,
        )
        await token.save()

async def on_transfer(operation: OperationModel):
    print('STUB', 'on_transfer', operation.parameters_json)

async def on_curate(operation: OperationModel):
    print('STUB', 'on_curate', operation.parameters_json)

async def on_collect(operation: OperationModel):
    print('STUB', 'on_collect', operation.parameters_json)
