# -*- coding: utf-8 -*-

import zmq
import iota
import matplotlib.pyplot as plt
import networkx as nx
from collections import deque
from db import r

COOR_ADDRESS = iota.Address('KPWCHICGJZXKE9GSUDXZYUAPLHAKAHYHDXNPHENTERYMMBQOPSQIDENXKLKCEYCPVTZQLEEJVYJZV9BWU')
DEPTH_TO_DRAW = 30
APPROVEE_TO_DRAW = 1

class Tangle:
    def __init__(self, db):
        self.g = nx.MultiDiGraph()
        self.db = db
        self.vis = set()
        self.graph_backlog = deque()
        self.zq = None

        self.init_zmq()

    def init_zmq(self):
        self.context = zmq.Context()
        self.zq = self.context.socket(zmq.SUB)
        self.zq.setsockopt(zmq.LINGER, 0)
        self.zq.connect('tcp://localhost:5556')
        self.zq.setsockopt(zmq.SUBSCRIBE, b'tx')
        self.zq.setsockopt(zmq.SUBSCRIBE, b'lmsi')
        self.zq.setsockopt(zmq.SUBSCRIBE, b'lmhs')

    def add_tx_to_tangle(self, tx, mindex=0, stop=0, search=False):
        txh = tx.hash[:8]

        if tx.hash not in self.vis:
            self.vis.add(tx.hash)
            self.g.add_node(txh, tx=tx, confirmed=tx.validity,
                trunk=tx.trunk_transaction_hash, timestamp=tx.timestamp)
            self.g.add_edge(txh, tx.branch_transaction_hash[:8])
            self.g.add_edge(txh, tx.trunk_transaction_hash[:8])

        # Is this bundle?
        self.g.node[txh]['style'] = 'filled'
        if 'fillcolor' not in self.g.node[txh]:
            if tx.last_index:
                self.g.node[txh]['fillcolor'] = '#f1c40f3f' if tx.current_index else '#f1c40f'
            else:
                self.g.node[txh]['fillcolor'] = '#3498db'

        # Does this tx change state?
        if tx.validity:
            self.g.node[txh]['fillcolor'] = '#2ecc71'

        if tx.address == COOR_ADDRESS:
            self.g.node[txh]['is_milestone'] = True
            self.g.node[txh]['milestone_index'] = mindex
            self.g.node[txh]['fillcolor'] = 'red'
            self.g.node[txh]['color'] = '#ff0000ff'
            self.g.node[txh]['style'] = 'filled'

            # Alpha the trunk in coordinator
            txh = tx.trunk_transaction_hash[:8]
            self.g.node[txh]['style'] = 'filled'
            self.g.node[txh]['fillcolor'] = '#ff00005f'

            if mindex:
                tr = self.db.get(tx.trunk_transaction_hash, 'transaction')
                self.graph_backlog.append((tr, DEPTH_TO_DRAW if search else 1))

                br = self.db.get(tx.branch_transaction_hash, 'transaction')
                self.graph_backlog.append((br, DEPTH_TO_DRAW if search else 1))
        else:
            if stop:
                tr = self.db.get(tx.trunk_transaction_hash, 'transaction')
                self.graph_backlog.append((tr, stop-1))

                br = self.db.get(tx.branch_transaction_hash, 'transaction')
                self.graph_backlog.append((br, stop-1))

    def add_milestone_to_tangle(self, milestone_index, search=True):
        index, milestone = self.db.get(milestone_index, 'milestone')
        tx = self.db.get(milestone, 'transaction')

        self.add_tx_to_tangle(tx, index, search=search)

    def update_backlog(self, revisit=False):
        count = 0
        while self.graph_backlog:
            tx, stop = self.graph_backlog.popleft()
            if tx.hash not in self.vis or revisit:
                self.add_tx_to_tangle(tx, stop=stop)
            count += 1
            if count % 20 == 0:
                print(count, len(self.graph_backlog))

if __name__ == '__main__':
    t = Tangle(r)

    for i in range(302292, 302280, -1):
        t.add_milestone_to_tangle(i)
    for i in range(302270, 302281):
        t.add_milestone_to_tangle(i, False)

    t.update_backlog()

    print('[*] Start to plot it')
    pd = nx.nx_pydot.to_pydot(t.g, strict=True)
    pd.set_strict(True)
    pd.write_jpg('/tmp/output.jpg')

    count = 0
    while True:
        recv = t.zq.recv().decode('utf-8').split(' ')

        tag = recv[0]
        txh = recv[1]

        t.db.init()
        if tag == 'lmsi':
            mindex = int(recv[2])
            t.add_milestone_to_tangle(mindex)
            t.update_backlog(revisit=True)

            recv = t.zq.recv().decode('utf-8').split(' ')

            tag = recv[0]
            txh = recv[1]
            txh = '%d %s' % (mindex, txh)
        else:
            tx = t.db.get(iota.Hash(txh), 'transaction')
            t.add_tx_to_tangle(tx)

        print(tag, txh)

        count += 1
        if count % 10 == 0:
            print('[*] Start to plot it')
            pd = nx.nx_pydot.to_pydot(t.g, strict=True)
            pd.set_strict(True)
            pd.write_jpg('/tmp/output.jpg')
