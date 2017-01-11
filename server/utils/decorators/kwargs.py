from pony.orm import db_session, get
from models.account import Account
from models.things import Being


# TODO think if this is useless?
def fetch_account(f):
    @db_session
    def fetcher(self, *args, **kwargs):

        print("Fetcher", args, kwargs)
        # If account is already supplied, don't do anything
        if "account" in kwargs:
            return f(self, *args, **kwargs)
        else:
            # To fetch the account, we need at least the account id
            if self.account_id is None:
                raise RuntimeError

            account = get(account for account in Account if account.id == self.account_id)
            if not account:
                raise RuntimeError

            return f(self, *args, account=account, **kwargs)

    return fetcher


def fetch_being(f):
    """
    Provides the decorated function with

    :param f: decorated function
    :return: decoration
    """
    @db_session
    def fetcher(self, *args, **kwargs):

        being = get(account.being for account in Account if account.id == self.account_id)
        #if not account



        pass

    return fetcher