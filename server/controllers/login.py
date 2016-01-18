__author__ = 'wizard'
from controllers.base import BaseController
from models.account import Account

class LoginController(BaseController):
    def __init__(self, *args):
        BaseController.__init__(self, *args)
        self.account = None
        self.state = 1
        self.greeting()
     

    def handle(self, message={}):
        try:
            BaseController.handle(self, message)
        except KeyError:
            key = message.get("k")
            value = message.get("v")
            if key != "msg" or len(value) == 0:
                continue
            # Received username
            if self.state == 1:
                self.account = Account.get(name=value)
                if self.account:
                    self.request_password()
                    self.state = 2
                else:
                    self.send_offtopic("Create new account y/n?")
                    self.state = 10

            # Received password
            elif self.state == 2:
                # Do something
                self.account.password

            # New account
            elif self.state == 10:
                if value.lower()[0] == "y":
                    self.state = 11
                else:
                    self.greeting()
                    self.state = 1

    def greeting(self):
        self.send_offtopic("Welcome to ropeclient dewdrop server. Please type your name.")

    def try_again(self):
        self.send_offtopic("Please try again.")
