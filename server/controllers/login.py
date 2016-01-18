__author__ = 'wizard'
from controllers.base import BaseController
from models.database import db
from models.account import Account
import os
import hashlib


class LoginController(BaseController):
    def __init__(self, *args):
        BaseController.__init__(self, *args)
        self.account = None
        self.state = 1
        self.static_salt = None
        self.dynamic_salt = None
        self.password = None # For creating a new account, store the password temporarily
        self.greeting()
     

    def handle(self, message={}):
        try:
            BaseController.handle(self, message)
        except KeyError:
            key = message.get("k")
            value = message.get("v")
            if key != "msg" or len(value) == 0:
                return

            # Received username
            if self.state == 1:
                self.account = Account.get(lambda account: account.name.lower() == value.lower())
                if self.account:
                    self.request_password()
                    self.state = 2
                else:
                    self.send_offtopic("Create new account with this name y/n?")
                    self.account = value
                    self.state = 10

            # Received password
            elif self.state == 2:
                # Do something
                if hashlib.sha256(self.account.password + self.dynamic_salt).hexdigest() == value:
                    self.send_offtopic("Login OK")
                else:
                    self.send_offtopic("Login fail")

            # New account
            elif self.state == 10:
                if value.lower()[0] == "y":
                    self.request_password(True, False)
                    self.state = 11
                else:
                    self.greeting()
                    self.state = 1

            elif self.state == 11:
                self.password = value

                self.request_password(False)
                self.state = 12

            elif self.state == 12:
                dynamic_password = hashlib.sha256(self.password + self.dynamic_salt).hexdigest()
                if dynamic_password == value:
                    self.state = 1
                    self.send_offtopic("New account has been created, you may now login.")
                    self.greeting()
                    account = Account(name=self.account,
                                      password=self.password,
                                      salt=self.static_salt)
                    db.commit()


                else:
                    self.send_offtopic("Password mismatch. Account not created.")
                    self.greeting()
                    self.state = 1

    def greeting(self):
        self.send_offtopic("Welcome to ropeclient dewdrop server. Please type your name.")

    def try_again(self):
        self.send_offtopic("Please try again.")

    def request_password(self, clear_static=True, dynamic=True):
        if isinstance(self.account, Account):
            self.static_salt = self.account.salt
        else:
            if clear_static or not self.static_salt:
                self.static_salt = hashlib.sha256(os.urandom(256)).hexdigest()

        if dynamic:
            self.dynamic_salt = hashlib.sha256(os.urandom(256)).hexdigest()
        else:
            self.dynamic_salt = None

        self.send([{'k': "oft", "v": "Please type your password"},
                   {'k': 'pwd',
                    'ss': self.static_salt,
                    'ds': self.dynamic_salt}])