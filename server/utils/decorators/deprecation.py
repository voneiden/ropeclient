import logging

def deprecated(f):
    warned = False
    def warn(*args, **kwargs):
        if not warned:
            logging.warn("Using deprecated function {}".format(str(f)))
            warned = True
        return f(*args, **kwargs)
        
    return warn

