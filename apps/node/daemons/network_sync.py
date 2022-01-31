import asyncio
import logging
import random

from aiohttp import ClientSession
from apscheduler.schedulers.blocking import BlockingScheduler

from pychain.node.config import settings
from pychain.node.db import Database
from pychain.node.models import Node


logging.basicConfig(
    datefmt="%H:%M:%S",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(settings.log_dir / "network_sync.log"),
    ],
)
# Suppress apscheduler log messages
logging.getLogger("apscheduler").setLevel(logging.WARNING)


log = logging.getLogger(__file__)
log.setLevel(settings.log_level)


async def network_sync() -> None:
    db = Database(host=settings.db_host, password=settings.db_password)
    Node.db = await db.init()
    Node.boot_node = Node(0, settings.boot_node_address)

    async with ClientSession() as session:
        if not (client := await db.get_client()):
            log.info("Sending join request to %s", Node.boot_node.address)
            client = await Node.boot_node.join_network(session)
            await db.set_client(client.address, client.guid)
            log.debug("Joined network as %s", client)

        log.debug("Connected to network as %s", client)

        for peer in (peers := await client.get_peers(session)):
            await db.ensure_node(peer.address, peer.guid)
            old_max_guid_node = await db.get_max_guid_node()
            new_max_guid_peer = await peer.sync(client.guid, old_max_guid_node, session)
            await db.ensure_node(new_max_guid_peer.address, new_max_guid_peer.guid)

    log.info("client: %s", client)
    log.info("max guid: %s", await db.get_max_guid())
    log.info("peers: %s", [int(p.guid) for p in peers])
    log.info("-" * 10)


def main() -> None:
    """ """
    if settings.is_boot_node:
        log.debug("Boot nodes do not perform network sync")
    else:
        asyncio.run(network_sync())


if __name__ == "__main__":
    jitter = random.randint(1, settings.network_sync_jitter)
    network_sync_interval = settings.network_sync_interval + jitter
    scheduler = BlockingScheduler()
    scheduler.add_job(main, trigger="interval", seconds=network_sync_interval)
    scheduler.start()
