#!/usr/bin/env python

import asyncio
import websockets
import json
import logging

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
    def __init__(self, websocket, path):
        self.account = None
        self.websocket = websocket
        self.path = path
        self.controller = LoginController(self)

    #@asyncio.coroutine
    def send(self, payload):
        print("Enter send", self, payload )
        asyncio.ensure_future(self.websocket.send(payload))
        print("Send yield return")

    @asyncio.coroutine
    def recv(self):
        print("Enter recv")
        while True:
            print("Listening..")
            message = yield from self.websocket.recv()
            print("Received: ", message)
            if message is None:
                break


class ConnectionHandler(object):
    @asyncio.coroutine
    def connection(self, websocket, path):
        c = Connection(websocket, path)
        print("Connection established", websocket, path)
        #yield from c.send(json.dumps(test_payload))
        print("Sent moro")
        yield from c.recv()
        print("Erp")


def run():
    handler = ConnectionHandler()
    server = websockets.serve(handler.connection, 'localhost', 8090)
    logging.basicConfig(level=logging.DEBUG)
    asyncio.get_event_loop().set_debug(enabled=True)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    run()