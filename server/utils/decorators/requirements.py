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
            if self.universe_id in self.account_id.god_universes:
                return f(self, *args, **kwargs)
        raise PermissionError

    return is_gamemaster


def is_being(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def check_is_being(self, *args, **kwargs):
        # TODO
        return f(self, *args, **kwargs)

    return check_is_being


def soul(f):
    """
    Decorator for limiting a command to a being only.

    :param f:
    :return:
    """

    def is_soul(self, *args, **kwargs):
        # TODO
        return f(self, *args, **kwargs)

    return is_soul