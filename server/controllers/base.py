import asyncio
import warnings
import json
import pony.orm
import logging
from utils.messages import *


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

    @staticmethod
    def convert_content(message_class, content):
        """
        Converts content to message objects. Content can be either string or a database (message) model

        :param message_class: Message class to convert into
        :param content: Content to be converted
        :return:
        """
        if isinstance(content, str):
            return message_class(content)
        elif isinstance(content, pony.orm.core.Entity):
            return message_class.from_model(content)
        else:
            raise ValueError("Unknown content: {}".format(content))

    def send_offtopic(self, *offtopic_lines, clear=False):
        """
        Converts and sends offtopic messages

        :param offtopic_lines: Valid offtopic content *args
        :param clear: Send along with a clear message
        :return:
        """
        logging.info("Sending offtopic")

        messages = [self.convert_content(OfftopicMessage, line) for line in offtopic_lines]

        # If clear is requested, clear the offtopic view
        if clear:
            messages.insert(0, ClearOfftopic())

        self.send_messages(*messages)

        logging.info("Success")

    def send_ontopic(self, *ontopic_lines):
        """
        Converts and sends ontopic messages

        :param ontopic_lines: Valid ontopic content *args
        :return:
        """
        logging.info("Sending ontopic")

        messages = [self.convert_content(OntopicMessage, line) for line in ontopic_lines]
        self.send_messages(*messages)

        logging.info("Success")

    def send(self, message):
        warnings.warn("Deprecated method", DeprecationWarning)
        self.connection.send(json.dumps(message))

    def send_messages(self, *args):
        messages_list = [message.__dict__ for message in args]
        self.connection.send(json.dumps(messages_list))

    def syntax_error(self):
        self.send_offtopic("Come again?")