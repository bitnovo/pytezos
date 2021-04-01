import logging

from hic_et_nunc_dapp.types.KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton.parameter.transfer import Transfer
from pytezos_dapps.models import HandlerContext

logger = logging.getLogger(__name__)


async def on_transfer(transfer: HandlerContext[Transfer]):
    for tr in transfer.parameter:
        tr = tr[1][0]
        for tx in tr.txs:
            print(tx)
