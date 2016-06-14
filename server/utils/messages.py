class OfftopicMessage(object):
    def __init__(self, text):
        self.k = "oft"
        self.v = text


class PasswordRequest(object):
    def __init__(self, static_salt, dynamic_salt=None):
        self.k = "pwd"
        self.ss = static_salt
        self.ds = dynamic_salt
