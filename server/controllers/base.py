import asyncio
import warnings
import json
import pony.orm
import logging
from utils.messages import *


class BaseController(object):
    def __new__(cls, *args):
        instance = super().__new__(cls)
        commands = {}
        startswith = {}
        instance._commands = commands
        instance._startswith = startswith
        instance._dynamic_commands = []

        # Loop through all class methods
        for name, method in cls.__dict__.items():

            # Check for static commands
            if hasattr(method, "_commands"):

                # Bind all commands to method, raise KeyError on duplicates
                for handle in method._commands:
                    if handle in commands:
                        raise KeyError("Duplicate key in commands")
                    commands[handle] = method

            # Check for dynamic commands
            if hasattr(method, "_dynamic_command"):
                instance._dynamic_commands.append(method)

            if hasattr(method, "_startswith"):
                for command in method._startswith:
                    if command in startswith or command in instance._dynamic_commands:
                        raise KeyError("Duplicate key in startswith or dynamic commands")
                    startswith[command] = method

        print("Instance handles:", instance._commands)
        return instance

    def __init__(self, connection, runtime):
        self.connection = connection
        self.account_id = None
        self.runtime = runtime

    def handle(self, message):
        assert "k" in message
        if message.k == "pit":
            pass
        elif message.k == "pnt":
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

    def stop(self):
        logging.info("Stopping base controller for account: ", self.account_id)