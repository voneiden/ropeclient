#!/usr/bin/env python
"""
    Login controller for ropeclient server
    Copyright (C) 2010 - 2016  Matti Eiden

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import hashlib
import logging
from controllers.base import BaseController
from controllers.menu import MenuController
from utils.messages import OfftopicMessage, PasswordRequest
from utils.decorators.kwargs import fetch_account
from utils.autonumber import AutoNumber
from models.database import db
from models.account import Account
from pony.orm import db_session


class State(AutoNumber):
    login_username = ()          # Greeted by login and username prompt, expecting username
    login_password = ()          # Matching Account was found, expecting password
    create_account = ()          # Matching Account not found, expecting yes/no to create new account
    create_password = ()         # Expecting password hashed with static salt
    create_password_repeat = ()  # Expecting double hashed password with static and dynamic salt


class LoginController(BaseController):
    def __init__(self, connection):
        BaseController.__init__(self, connection)
        self.account_name = None
        self.state = State.login_username
        self.static_salt = None
        self.dynamic_salt = None
        self.password = None  # For creating a new account, store the password temporarily
        self.greeting()


    @fetch_account
    def hash_password_with_salt(self, account, password=None, salt=None):
        """
        Hash a password with a salt using SHA-256

        :param account:
        :param password:
        :param salt:
        :return:
        """

        if password is None:
            password = account.password

        if salt is None:
            salt = account.salt

        print("password:", password)
        print("salt:", salt)
        return hashlib.sha256((password + salt).encode("utf8")).hexdigest()

    # TODO: Optimize db session?
    # TODO: BaseController could return a boolean instead of raising
    # TODO:
    @db_session
    def handle(self, message={}):
        """
        Handle a received message in login state

        :param message:
        :return:
        """
        try:
            BaseController.handle(self, message)
        except KeyError:
            key = message.get("k")
            value = message.get("v")
            if key != "msg" or len(value) == 0:
                return

            # State - Login username
            if self.state == State.login_username:
                account = Account.get(lambda account: account.name.lower() == value.lower())

                if account:
                    self.account_id = account.id
                    self.request_password()
                    self.state = State.login_password
                else:
                    self.send_offtopic("Create new account with this name y/n?")
                    self.account_name = value
                    self.state = State.create_account

            # State - Login password
            elif self.state == State.login_password:
                account = self.fetch_account()
                # TODO TODO TODO lets make a decorator for fetch account (args) and modify these states to work with the autohandler
                if self.hash_password_with_salt(salt=self.dynamic_salt) == value:
                    self.send_offtopic("Login OK")
                    # Set controller to menu controller
                    self.connection.controller = MenuController(self.connection, self.account_id)
                    return

                else:
                    logging.info("Expected password: {}".format(
                        self.hash_password_with_salt(salt=self.dynamic_salt)))
                    logging.info("Received password: {}".format(value))
                    self.send_offtopic("Login fail")
                    self.state = State.login_username
                    self.greeting()


            # State - Create account
            elif self.state == State.create_account:
                if value.lower()[0] == "y":
                    self.request_password(account=None, clear_static=True, dynamic=False)
                    self.state = State.create_password
                else:
                    self.greeting()
                    self.state = State.login_username

            # State - Create account - password (1st)
            elif self.state == State.create_password:
                self.password = value
                logging.info("Received password 1: {}".format(value))

                self.request_password(account=None, clear_static=False, dynamic=True)
                self.state = State.create_password_repeat

            # State - Create account - password repeat
            elif self.state == State.create_password_repeat:
                dynamic_password = self.hash_password_with_salt(account=None, password=self.password, salt=self.dynamic_salt)
                logging.info("Received password 2: {}, type {} ".format(value, type(value)))
                print("expected:", dynamic_password, type(dynamic_password))

                if dynamic_password == value:
                    self.state = State.login_username
                    self.send_offtopic("New account has been created, you may now login.")
                    self.greeting()
                    account = Account(name=self.account_name,
                                      password=self.password,
                                      salt=self.static_salt)
                    db.commit()

                else:
                    self.send_offtopic("Password mismatch. Account not created.")
                    self.greeting()
                    self.state = State.login_username

    def greeting(self):
        self.send_offtopic("Welcome to ropeclient dewdrop server. Please type your name.")

    def try_again(self):
        self.send_offtopic("Please try again.")

    @fetch_account
    def request_password(self, account, clear_static=True, dynamic=True):
        if isinstance(account, Account):
            self.static_salt = account.salt
        else:
            if clear_static or not self.static_salt:
                self.static_salt = hashlib.sha256(os.urandom(256)).hexdigest()

        if dynamic:
            self.dynamic_salt = hashlib.sha256(os.urandom(256)).hexdigest()
        else:
            self.dynamic_salt = None

        self.send_messages(OfftopicMessage("Please type your password"),
                           PasswordRequest(self.static_salt, self.dynamic_salt))