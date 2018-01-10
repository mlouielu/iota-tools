# -*- coding: utf-8 -*-

from db import r as tangle


def get_latest_30_milestone_hash():
    index, milestone = tangle.latest('milestone')

    for i in range(index, index - 30, -1):
        m = tangle.get(i, 'milestone')
        tx = tangle.get(m[1], 'transaction')
        next_trunk = tangle.get(get_trunk(tx).hash, 'transaction')
        print(m[0], m[1], tx.validity, next_trunk.hash, next_trunk.validity)


def get_two_latest_milestone_transaction():
    index, milestone = tangle.latest('milestone')

    m1 = tangle.get(tangle.get(index - 1, 'milestone')[1], 'transaction')
    m2 = tangle.get(tangle.get(index, 'milestone')[1], 'transaction')

    return m1, m2

def get_trunk(tx):
    while tx.current_index != tx.last_index:
        tx = tangle.get(tx.trunk_transaction_hash, 'transaction')

    return tangle.get(tx.trunk_transaction_hash, 'transaction')


if __name__ == '__main__':
    m1, m2 = get_two_latest_milestone_transaction()
    print(m1.hash, m2.hash)
    print(get_trunk(m1).hash)

    get_latest_30_milestone_hash()
