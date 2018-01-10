# -*- coding: utf-8 -*-
# Check transaction solid

import datetime
import sys
import iota
from db import r as tangle


if __name__ == '__main__':
    hash = sys.argv[1]

    index, mh = tangle.latest('milestone')[1]
    print(f'{index}, {mh[:20]}')
    if len(hash) == 81:
        tx = tangle.get(iota.Hash(hash), 'transaction')
        print(tx.hash, tx.solid, tx.validity)
    else:
        addrs = tangle.get(iota.Address(hash[:81]), 'address')
        for txh in addrs:
            tx = tangle.get(txh, 'transaction')
            print(f'{tx.hash[:20]}..., status: {tx.validity}, value: {tx.value}',
                  f'time: {datetime.datetime.fromtimestamp(tx.timestamp).strftime("%H:%M:%S")}',
                  f'approvee: {len(list(tangle.get(txh, "approvee")))}')
