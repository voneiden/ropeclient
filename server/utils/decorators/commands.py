class Commands(object):
    def __init__(self, *commands, startswith=None):
        self.commands = commands
        self.startswith = startswith if startswith else None

    def __call__(self, f):
        f._commands = self.commands
        if self.startswith:
            f._startswith = self.startswith
        return f


def dynamic_command(f):
    f._dynamic_command = True
    return f

"""
def handler_controller(controller_cls):
    handles = {}
    if not hasattr(controller_cls, "_handles"):
        controller_cls._handles = handles

    for name, method in controller_cls.__dict__.copy().items():
        if hasattr(method, "_handles"):
            for handle in method._handles:
                if handle in handles:
                    raise KeyError("Duplicate key in handler")
                handles[handle] = method
"""