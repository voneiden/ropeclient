#!/usr/bin/env python
import asyncio
import websockets
import json
import logging
from controllers.login import LoginController
from models.database import db, db_mapping
from models.universe import Planet

SECURE = False
DEVELOPMENT = True

if SECURE:
    import ssl

if DEVELOPMENT:
    import setup
    db.bind('sqlite', ':memory:')
    db_mapping()
    setup.setup_development_environment()


else:
    db.bind("sqlite", "database.sqlite")
    db_mapping()


class Runtime(object):
    def __init__(self):
        self.controller_mapping = {}

    def add_controller(self, universe_id, account_id, controller):
        if universe_id not in self.controller_mapping:
            self.controller_mapping[universe_id] = {}
        self.controller_mapping[universe_id][account_id] = controller

    def remove_controller(self, universe_id, account_id):
        if universe_id in self.controller_mapping and account_id in self.controller_mapping[universe_id]:
            del self.controller_mapping[universe_id][account_id]

    def find_controllers(self, universe_id):
        return self.controller_mapping.get(universe_id, {}).values()

runtime = Runtime()


class Connection(object):
    def __init__(self, websocket, address):
        """
        Connection object that is created when a new client connects.

        :param websocket: Websocket bound to the connection
        :param address: Address of the connection
        :return:
        """
        self.account = None
        self.websocket = websocket
        self.address = address
        self.controller = LoginController(self, runtime)
        logging.info("Connection established to address [{}]".format(str(address)))

    def send(self, payload):
        """
        Send a raw payload in the websocket

        :param payload: Payload to be sent
        :type payload: str
        :return:
        """
        logging.info("Queueing payload [{payload}] to address [{address}]".format(payload=payload, address=self.address))
        asyncio.ensure_future(self.websocket.send(payload))

    @asyncio.coroutine
    def recv(self):
        """
        Ready to receive data from the websocket. Passes the data to a controller handler.

        :return:
        """
        logging.info("Handling requests from " + self.address)
        while True:
            raw_message = yield from self.websocket.recv()
            if not raw_message:
                break
            logging.info("Received payload from address [{address}]: {message}".format(address=self.address, message=raw_message))
            try:
                message = json.loads(raw_message)
            except ValueError:
                logging.error("Unable to parse message")
                continue
            self.controller.handle(message)
            if message is None:
                break

        self.controller.stop()


class ConnectionHandler(object):
    @asyncio.coroutine
    def connection(self, websocket, path):
        c = Connection(websocket, str(websocket.remote_address[0]))
        logging.info("Connection established: %s", str(websocket.remote_address[0]))
        yield from c.recv()


# Python bug 23057
def display_startup_info():
    print("\n\n##### NOTE #####\n")
    print("On windows machines the server can be stopped using CTRL+break")
    print("Due to Python bug 23057 CTRL+C does not work.")
    print("\n################\n\n")


def start_tasks():
    #Planet.start_tasks(runtime)
    pass


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

    # Python bug 23057 workaround for windows
    #asyncio.async(windows_dumb_do_nothing_routine())

    loop.run_until_complete(server)
    if SECURE:
        secure_server = websockets.serve(handler.connection, 'localhost', 8091, ssl=sc)
        loop.run_until_complete(secure_server)

    loop.call_later(1, display_startup_info)
    loop.call_later(1, start_tasks)
    loop.run_forever()


if __name__ == "__main__":
    run()
