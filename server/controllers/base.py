import asyncio
import json


class BaseController(object):
    def __init__(self, connection):
        self.connection = connection

    def handle(self, message={}):
        assert "k" in message
        if "k" == "png":
            pass
        else:
            raise KeyError


    def request_password(self):
        self.send([{'k': "oft", "v": "Please type your password"},
                   {'k': 'pwd'}])

    def send_offtopic(self, text):
        print("Sending..")
        self.send({"k": "oft", "v": text})
        print("SeNT")

    def send_ontopic(self, text):
        self.send({"k": "ont", "v": text})

    def send(self, message):
        print("SENDSEND")
        self.connection.send(json.dumps(message))
        print("YIELD!")