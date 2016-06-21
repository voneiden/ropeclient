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
            if self.universe in self.account.god_universes:
                return f(self, *args, **kwargs)
        raise PermissionError

    return is_gamemaster


def being(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def is_being(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return is_being


def soul(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def is_soul(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return is_soul