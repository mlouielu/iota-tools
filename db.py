import iotapy

r = iotapy.storage.providers.rocksdb.RocksDBProvider('/var/db/iota/mainnetdb', '/var/db/iota/mainnetdb.log', read_only=True)
r.init()
