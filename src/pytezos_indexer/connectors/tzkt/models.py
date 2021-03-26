from tortoise import Model, fields

"""
  {
    "type": "transaction",
    "id": 43848612,
    "level": 1400108,
    "timestamp": "2021-03-25T13:04:46Z",
    "block": "BM8xHMUyz8coDJepDoL15sKGwiiZDn3Sg8aipPDXaEGiiW1rs8F",
    "hash": "oowvWBL6TbvWqTpFQ5WGj8adjoHYEKWdizZAv81S725mYkPxGnP",
    "counter": 82721,
    "initiator": {
      "address": "tz1PnbhBb2TV4tJjX1BpAScx8rPk2YAcc5VD"
    },
    "sender": {
      "alias": "Dexter kUSD/XTZ",
      "address": "KT1AbYeDbjjcAnV1QK7EZUUdqku77CdkTuv6"
    },
    "nonce": 0,
    "gasLimit": 0,
    "gasUsed": 26616,
    "storageLimit": 0,
    "storageUsed": 0,
    "bakerFee": 0,
    "storageFee": 0,
    "allocationFee": 0,
    "target": {
      "alias": "kUSD",
      "address": "KT1K9gCRgaLRFKTErYt1wVxA3Frb9FjasjTV"
    },
    "amount": 0,
    "parameter": {
      "entrypoint": "transfer",
      "value": {
        "to": "tz1PnbhBb2TV4tJjX1BpAScx8rPk2YAcc5VD",
        "from": "KT1AbYeDbjjcAnV1QK7EZUUdqku77CdkTuv6",
        "value": "2173213521457339404110"
      }
    },
    "status": "applied",
    "hasInternals": false,
    "parameters": "{\"entrypoint\":\"transfer\",\"value\":{\"prim\":\"Pair\",\"args\":[{\"bytes\":\"011615e137f0a86dadbe9c39093d87f13af5b627a300\"},{\"prim\":\"Pair\",\"args\":[{\"bytes\":\"00002d7f60f6c60c810b986ceff0084845d688309085\"},{\"int\":\"2173213521457339404110\"}]}]}}"
  },
"""

class Transaction(Model):
    id = fields.IntField(pk=True)
    type = fields.CharField(128, null=True)
    level = fields.IntField(null=True)
    timestamp = fields.DatetimeField(null=True)
    block = fields.CharField(128, null=True)
    hash = fields.CharField(128, null=True)
    counter = fields.IntField(null=True)
    initiator_address = fields.CharField(128, null=True)
    sender_address = fields.CharField(128, null=True)
    sender_alias = fields.CharField(128, null=True)
    nonce = fields.IntField(null=True)
    gas_limit = fields.IntField(null=True)
    gas_used = fields.IntField(null=True)
    baker_fee = fields.IntField(null=True)
    storage_fee = fields.IntField(null=True)
    allocation_fee = fields.IntField(null=True)
    target_address = fields.CharField(128, null=True)
    target_alias = fields.CharField(128, null=True)
    amount = fields.IntField(null=True)
    status = fields.CharField(128, null=True)
    has_internals = fields.BooleanField(null=True)
    parameters = fields.CharField(1024, null=True)

    @classmethod
    def from_json(cls, kwargs):
        kwargs['initiator_address'] = kwargs.get('initiator', {}).get('address')
        kwargs['sender_address'] = kwargs.get('sender', {}).get('address')
        kwargs['sender_alias'] = kwargs.get('sender', {}).get('alias')
        kwargs['gas_limit'] = kwargs.get('gasLimit')
        kwargs['gas_used'] = kwargs.get('gasUsed')
        kwargs['baker_fee'] = kwargs.get('bakerFee')
        kwargs['storage_fee'] = kwargs.get('storageFee')
        kwargs['allocation_fee'] = kwargs.get('allocationFee')
        kwargs['target_address'] = kwargs.get('target', {}).get('address')
        kwargs['target_alias'] = kwargs.get('target', {}).get('alias')
        kwargs['has_internals'] = kwargs.get('hasInternals')
        return cls(**kwargs)
