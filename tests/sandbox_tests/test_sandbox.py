from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.sandbox.parameters import sandbox_addresses, EDO, FLORENCE


# NOTE: Node won't be wiped between tests so alphabetical order of method names matters
class SandboxTestCase(SandboxedNodeTestCase):

    def test_1_activate_protocol(self) -> None:
        block = self.client.shell.block()
        self.assertIsNotNone(block['header'].get('content'))

    def test_2_bake_empty_block(self) -> None:
        self.bake_block()

    def test_3_create_transaction(self) -> None:
        opg = self.client.transaction(
            destination=sandbox_addresses['bootstrap3'],
            amount=42,
        ).fill().sign().inject(min_confirmations=0)
        self.assertIsNotNone(self.client.shell.mempool.pending_operations[opg['hash']])

    def test_4_bake_block(self) -> None:
        self.bake_block()
        bootstrap2 = self.client.shell.contracts[sandbox_addresses['bootstrap3']]()
        self.assertEqual('4000000000042', bootstrap2['balance'])

    def test_5_rollback(self) -> None:
        self.activate(EDO, reset=True)
        bootstrap2 = self.client.shell.contracts[sandbox_addresses['bootstrap3']]()
        self.assertEqual('4000000000000', bootstrap2['balance'])
