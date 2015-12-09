__author__ = 'wizard'
from controllers.base import BaseController


class LoginController(BaseController):
    def __init__(self, *args):
        BaseController.__init__(self, *args)
        self.state = 0
        self.handle({"k": None})

    def handle(self, message={}):
        try:
            BaseController.handle(self, message)
        except KeyError:
            key = message.get("k")
            if self.state == 0:
                self.greeting()
                self.state = 1
            # Received username
            elif self.state == 1:
                if key == "msg":
                    self.request_password()
                    self.state = 2
                else:
                    self.try_again()

            # Received password
            elif self.state == 2:
                pass

            # New account
            elif self.state == 10:
                pass

    def greeting(self):
        self.send_offtopic("Welcome to ropeclient dewdrop server. Please type your name.")

    def try_again(self):
        self.send_offtopic("Please try again.")