import hashlib, os


def hash_password(password, salt=""):
    return hashlib.sha256((password + salt).encode("utf8")).hexdigest()


def generate_salt():
    return hashlib.sha256(os.urandom(256)).hexdigest()

