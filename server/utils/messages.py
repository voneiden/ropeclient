import datetime
import random
import re
from models.account import Account
from models.things import Being
from pony.orm import db_session

@db_session
def nameReplacer(controller, match):
    being_id = int(match.groups()[0])
    print(being_id, controller.being_id)
    who = None
    verb = None
    if being_id == controller.being_id:
        who = "You"
        verb = match.groups()[1]
    else:
        who = "Somebody"
        verb = match.groups()[2]

    return "{who} {verb}".format(who=who, verb=verb)


# TODO capitalize sentences

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
    @db_session
    def from_model(cls, model, controller):
        being = Being[model.being.id]
        account = being.account
        account_id = account.id if account else None

        # Parse text TODO some sort of re.subtract
        #model.
        text = re.sub("{name:(\d+):(.+?):(.+?)}", lambda match: nameReplacer(controller, match), model.text)

        return cls(text=text, timestamp=model.timestamp, account=account_id)


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
            account = account.name
        self.a = account

    @classmethod
    def from_model(cls, model, controller):
        #account_id = model.account.id if model.account else None
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


class PlayerList(object):
    def __init__(self, players):
        """
        @param players: List of player objects {name, typing
        @type players: list

        """
        self.k = "pll"
        self.v = players


class PlayerIsTyping(object):
    def __init__(self, account):
        if isinstance(account, Account):
            account = account.name
        self.k = "pit"
        self.a = account


class PlayerNotTyping(object):
    def __init__(self, account):
        if isinstance(account, Account):
            account = account.name
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



