class OntopicMessage(object):
    def __init__(self, text, timestamp=None, account=None):
        self.k = "ont"
        self.v = text
        self.t = timestamp
        self.a = account

    @classmethod
    def from_model(cls, model):
        return cls(text=model.text, timestamp=model.timestamp, account=model.account)


class OfftopicMessage(object):
    def __init__(self, text, timestamp=None, account=None):
        self.k = "oft"
        self.v = text
        self.t = timestamp
        self.a = account

    @classmethod
    def from_model(cls, model):
        return cls(text=model.text, timestamp=model.timestamp, account=model.account)


class PasswordRequest(object):
    def __init__(self, static_salt, dynamic_salt=None):
        self.k = "pwd"
        self.ss = static_salt
        self.ds = dynamic_salt
