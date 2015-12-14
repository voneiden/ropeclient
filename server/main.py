#!/usr/bin/env python
import asyncio
import websockets
import json
import logging

SECURE = False

if SECURE:
    import ssl

from controllers.login import LoginController
from models.database import db
db.bind("sqlite", "database.sqlite")


#test_message = {
#    "raw": "This is a <green>test<reset> message from the server!",
#    "owner": "server",
#    "stamp": 1435959022.9176872
#}#
#
#test_payload = {
#    'k': 'oft',
#    'v': test_message
#}


class Connection(object):
    def __init__(self, websocket, address):
        self.account = None
        self.websocket = websocket
        self.address = address
        self.controller = LoginController(self)

    #@asyncio.coroutine
    def send(self, payload):
        logging.info("Queueing payload to " + self.address)
        asyncio.ensure_future(self.websocket.send(payload))

    @asyncio.coroutine
    def recv(self):
        logging.info("Handling requests from " + self.address)
        while True:
            message = yield from self.websocket.recv()
            logging.info("Received payload from " + self.address + ": " + message)
            if message is None:
                break


class ConnectionHandler(object):
    @asyncio.coroutine
    def connection(self, websocket, path):
        c = Connection(websocket, str(websocket.remote_address[0]))
        logging.info("Connection established: %s", str(websocket.remote_address[0]))
        yield from c.recv()


def run():
    # Setup logging
    logger = logging.getLogger("")
    logger.handlers = []

    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s %(module)-10s:%(lineno)-3s %(levelname)-7s %(message)s',"%y%m%d-%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    logging.info("Logger configured")



    handler = ConnectionHandler()
    if SECURE:
        sc = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sc.load_cert_chain('selfsigned.cert', 'selfsigned.key')

    server = websockets.serve(handler.connection, 'localhost', 8090)
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    loop.run_until_complete(server)
    if SECURE:
        secure_server = websockets.serve(handler.connection, 'localhost', 8091, ssl=sc)
        loop.run_until_complete(secure_server)
    loop.run_forever()


if __name__ == "__main__":
    run()
