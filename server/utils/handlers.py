class Handlers(object):
    def __init__(self, *handles):
        self.handles = handles

    def __call__(self, f):
        f._handles = self.handles
        return f


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





