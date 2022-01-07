## Node Configuration
* `ADDRESS_CHECK_FREQUENCY` (optional, default: 25)
  * How many executions of peer_scan.py should occur before this node asks a peer what
    it's IP address is. This feature exists to handle the case where a client's IP
    address changes.

* `BOOT_NODES` (required)
  * Comma delimited list of nodes to use for bootstrapping to the network. Of the nodes
    provided, a randomly selected subset of `MAX_BOOT_NODES` will be used.
  * Example config: `BOOT_NODES=<URL or IP-address>:<port>,[<URL or IP-address>:<port>]`

* `DEDICATED_PEERS` (optional)
  * Hard coded list of comma delimited peers that this node should peer with.
  * Example config: `DEDICATED_PEERS=<URL or IP-address>:<port>,[<URL or IP-address>:<port>]`

* `IGNORED_PEERS` (optional)
  * Hard coded list of comma delimited peers that this node should NOT peer with.
  * Example config: `IGNORED_PEERS=<URL or IP-address>:<port>,[<URL or IP-address>:<port>]`

* `MAX_BOOT_NODES` (optional, default: 5)
  * The maximum number of boot nodes from `BOOT_NODES` to use.

* `MAX_PEERS` (optional, default: 10)
  * The maximum number of peers that this node will keep track of at any given time.

* `PEER_SCAN_INTERVAL` (optional, default: 60)
  * How many seconds should elapse between executions of peer_scan.py.

## Development Environment
```bash
$ docker-compose up --build

# Send request to boot node from client node 1
$ docker exec -it pychain_client_1_1 curl http://pychain-boot-1.com/api/v1/version

# Send request to client node 1 from boot node
$ docker exec -it pychain_boot_1_1 curl http://pychain-client-1.com/api/v1/version

# Tail logs to observe node behavior
$ docker exec -it pychain_client_1_1 tail -f /var/log/pychain/{api,peer_scan}.log
$ docker exec -it pychain_bootstrap_1_1 tail -f /var/log/pychain/{api,peer_scan}.log
```

## Architecture
```
Each node is running
- nginx: reverse proxy to API
- uvicorn: Serving API written in FastAPI
- redis: Stores node settings
- python: Long running `peer_scan` process that discovers peers and stores info in redis

All of these processes are managed by supervisor.
```

## Development notes
```
TODO:
Add a some sort of identifier to the response from /api/v1/status that
  tells the caller that the callee is actually a node on the pychain
  network. Otherwise any server that responds to requests on that
  endpoint will be seen as a valid peer.

/api/v1/version returns the version of the pychain package the node is running.
Each node should determine if their peers are running a compatible version of
the software as their own before keeping them as a peer. Maybe there should be
a "capabilities" endpoint whose response gets added as an attribute to Peer
objects and those capabilities can be used to enable/disable certain features
when interacting with peer nodes.

Add support for basic message broadcasting between peers

For testing purposes, create a "beacon" node that all nodes alert when a message
  is broadcast. All nodes would tell the beacon that they received this message,
  Checking the beacon logs would allow us to confirm whether the broadcast was
  propogated to the entire network and how long it took for all nodes to see it.

Configure logrotate
```
