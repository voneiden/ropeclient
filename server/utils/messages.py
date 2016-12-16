import datetime
import random
from models.account import Account


class OntopicMessage(object):
    def __init__(self, text, timestamp=None, account=None):
        """
        Ontopic message is anything in-game related

        :param text: Text of the message
        :param timestamp: Optional UNIX timestamp
        :param account: Optional owner of the message (account or account id)
        :type text: str
        :type timestamp: float, datetime
        :type account: Account or int
        :return:
        """
        self.k = "ont"
        self.v = text

        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.timestamp()
        self.t = timestamp

        if isinstance(account, Account):
            account = account.id
        self.a = account

    @classmethod
    def from_model(cls, model):
        return cls(text=model.text, timestamp=model.timestamp, account=model.account)


class OfftopicMessage(object):
    def __init__(self, text, timestamp=None, account=None):
        """
        Offtopic message is anything non-game related

        :param text: Text of the message
        :param timestamp: Optional UNIX timestamp
        :param account: Optional owner of the message (account or account id)
        :type text: str
        :type timestamp: float, datetime
        :type account: Account or int
        :return:
        """
        self.k = "oft"
        self.v = text

        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.timestamp()
        self.t = timestamp

        if isinstance(account, Account):
            account = account.id
        self.a = account

    @classmethod
    def from_model(cls, model):
        return cls(text=model.text, timestamp=model.timestamp, account=model.account)


class PasswordRequest(object):
    def __init__(self, static_salt, dynamic_salt=None):
        """

        :param static_salt:
        :param dynamic_salt:
        :return:
        """
        self.k = "pwd"
        self.ss = static_salt
        self.ds = dynamic_salt


class PlayerIsTyping(object):
    def __init__(self, account):
        if isinstance(account, Account):
            account = account.id
        self.k = "pit"
        self.a = account


class PlayerNotTyping(object):
    def __init__(self, account):
        if isinstance(account, Account):
            account = account.id
        self.k = "pnt"
        self.a = account


class ClearOfftopic(object):
    def __init__(self):
        self.k = "clr"
        self.v = "oft"


class ClearOntopic(object):
    def __init__(self):
        self.k = "clr"
        self.v = "ont"


class ClearBoth(object):
    def __init__(self):
        self.k = "clr"
        self.v = "all"


class Ping(object):
    def __init__(self, value=None):
        if not value:
            value = random.random()
        self.k = "png"
        self.v = value


