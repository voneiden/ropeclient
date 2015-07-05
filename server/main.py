#!/usr/bin/env python

import asyncio
import websockets
import json

test_message = {
    "raw": "This is a <green>test<reset> message from the server!",
    "owner": "server",
    "stamp": 1435959022.9176872
}

test_payload = {
    'k': 'oft',
    'v': test_message
}
class ConnectionHandler(object):
    @asyncio.coroutine
    def connection(self, websocket, path):
        print("Connection established", websocket, path)
        yield from websocket.send(json.dumps(test_payload))
        print("Sent moro")
        while True:
            message = yield from websocket.recv()
            if message is None:
                break

            print("Received: ", message)


def run():
    handler = ConnectionHandler()
    server = websockets.serve(handler.connection, 'localhost', 8090)

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    run()