import asyncio
import json
import pony.orm
import logging

class BaseController(object):
    def __init__(self, connection):
        self.connection = connection
        self.account = None

    def handle(self, message={}):
        assert "k" in message
        if "k" == "png":
            pass
        else:
            raise KeyError


    def request_password(self):
        self.send([{'k': "oft", "v": "Please type your password"},
                   {'k': 'pwd'}])

    def send_offtopic(self, content):
        logging.info("Sending offtopic")
        if isinstance(content, str):
            self.send({"k": "oft", "v": content})
        elif isinstance(content, pony.orm.core.Entity):
            self.send({"k": "oft",
                       "v": content.text,
                       "t": content.timestamp,
                       "a": content.account})
        logging.info("Success")

    def send_ontopic(self, text):
        logging.info("Sending ontopic")
        self.send({"k": "ont", "v": text})

    def send(self, message):
        self.connection.send(json.dumps(message))