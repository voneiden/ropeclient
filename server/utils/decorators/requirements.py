def gamemaster(f):
    """
    Decorator for limiting a command to gamemasters only.

    :param f:
    :return:
    """
    def is_gamemaster(self, *args, **kwargs):
        """

        :param self:
        :param args:
        :param kwargs:
        :type self: controllers.play.PlayController
        :return:
        """
        if hasattr(self, "account") and hasattr(self, "universe"):
            if self.universe in self.account_id.god_universes:
                return f(self, *args, **kwargs)
        raise PermissionError

    return is_gamemaster


def is_being(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def is_being(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return is_being


def is_soul(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def is_soul(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return is_soul


def has_account(f):
    """
    Ensures that the called function has an account available

    :param f:
    :return:
    """
    def wrapper(self, *args, **kwargs):
        if not self or self.account_id is None:
            raise RuntimeError("The called method requires an account")
        return f(self, *args, **kwargs)

    return wrapper