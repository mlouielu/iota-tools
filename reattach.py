# -*- coding: utf-8 -*-

import sys
import requests
import iota
from db import r

HOST = 'http://localhost:14685'

bh = iota.Hash(sys.argv[1])
txhs = list(r.get(bh, 'bundle'))[::-1]

tips = requests.post(HOST, headers={'X-IOTA-API-VERSION': '1'}, json={
    'command': 'getTransactionsToApprove',
    'depth': 6}).json()
print(tips)

trunk_hash = iota.Hash(tips['trunkTransaction'])
branch_hash = iota.Hash(tips['branchTransaction'])    
data = {
    "command": "attachToTangle",
    "trunkTransaction": str(trunk_hash),
    "branchTransaction": str(branch_hash),
    "minWeightMagnitude": 16,
    "trytes": [str(r.get(i, 'transaction').as_tryte_string()) for i in txhs]
}

r = requests.post('http://localhost:14685', headers={'X-IOTA-API-VERSION': '1'}, json=data)
trytes = r.json()['trytes']
r = requests.post(HOST, headers={'X-IOTA-API-VERSION': '1'},
    json={'command': 'broadcastTransactions', 'trytes': trytes})
r = requests.post(HOST, headers={'X-IOTA-API-VERSION': '1'},
    json={'command': 'storeTransactions', 'trytes': trytes})
