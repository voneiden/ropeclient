#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
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

    Copyright 2010-2014Matti Eiden <snaipperi()gmail.com>
"""

import logging
import redis
#from core import Core
from redis import StrictRedis

class Database(object):
    """
    Subclass of StrictRedis that provides abstraction to accessing database data
    """
    def __init__(self, core=None, client=None, **kwargs):
        """ Provides customized access to redis database
        @param core: Core object
        @param client: StrictRedis object or none
        @param kwargs: StrictRedis kwargs
        @type core: Core
        @type client: StrictRedis
        @return:
        """


        if not client:
            logging.info("Connecting to redis database")
            self.client = redis.StrictRedis(**kwargs)
        else:
            self.client = client

        self.core = core

    def set(self, key, value):  #, *args):
        """ Set a string value in database

        @param key: Key of the object attribute
        @param value: Value to set the object attribute to
        @type key: str
        @type value: str
        @return:
        """
        assert isinstance(key, str)
        assert isinstance(value, str)

        return self.client.set(self.path(key), value)  #, *args)  # TODO: If this stuff causes NotImplementedError then implement it

    def get(self, key):
        """ Retrieve string value from database

        @param key: Key of the object attribute
        @return:
        """
        assert isinstance(key, str)

        result = self.client.get(self.path(key))
        if isinstance(result, bytes):
            result = result.decode("utf8")

        return result


    def mget(self, *keys):
        """ Retrieve multiple string values

        @param keys: List of keys to retrieve
        @type keys: (tuple, list)
        @return:
        """
        raise NotImplementedError #TODO str-byte assertion
        assert isinstance(keys, tuple) or isinstance(keys, list)
        assert all([isinstance(key, str) for key in keys])
        return self.client.mget(self.path(keys))

    def sadd(self, key, *values):
        """ Add member(s) to a set in database

        @param key: Key of the object attribute
        @param values: Values to add to the attribute
        @type key: str
        @type values: (list, tuple)
        @return:
        """

        assert isinstance(key, str)
        assert isinstance(values, list) or isinstance(values, tuple)

        return self.client.sadd(self.path(key), *values)

    def srem(self, key, *values):
        """ Add member(s) to a set in database

        @param key: Key of the object attribute
        @param values: Values to add to the attribute
        @type key: str
        @type values: (list, tuple)
        @return:
        """

        assert isinstance(key, str)
        assert isinstance(values, list) or isinstance(values, tuple)

        return self.client.srem(self.path(key), *values)

    def incr(self, key):
        """
        Increment a key

        @param key: Key to be incremented
        @return: New value
        """
        assert isinstance(key, str)
        return self.client.incr(self.path(key))

    def hget(self, key, hkey):
        """
        Hash Get
        @param key: key name
        @param hkey: hash key name
        @return: value
        """
        assert isinstance(key, str)
        assert isinstance(hkey, str)
        result = self.client.hget(self.path(key), hkey)

        if isinstance(result, bytes):
            result = result.decode("utf8")

        return result

    def hset(self, key, hkey, hvalue):
        """
        Hash set
        @param key: key name
        @param hkey: hash key name
        @param value: hash key value
        @return:
        """
        assert isinstance(key, str)
        assert isinstance(hkey, str)
        assert isinstance(hvalue, str) or isinstance(hvalue, int) or isinstance(hvalue, float)
        return self.client.hset(self.path(key), hkey, hvalue)

    def smembers(self, key):
        assert isinstance(key ,str)
        #return [member.decode("utf8") for member in self.client.smembers(self.path(key))]
        return self.client.smembers(self.path(key))

    def list(self):
        #return [ident.decode("utf8") for ident in self.client.smembers("{}.list".format(self.path()))]
        #return self.client.smembers("{}.list".format(self.path()))
        return self.client.lrange("{}.list".format(self.path()), 0, -1)

    def lpush(self, key, *values):
        assert isinstance(key, str)
        assert isinstance(values, tuple)
        return self.client.lpush(self.path(key), *values)

    def rpush(self, key, *values):
        assert isinstance(key, str)
        assert isinstance(values, tuple)
        return self.client.rpush(self.path(key), *values)

    def lrange(self, key, start, stop):
        assert isinstance(key, str)
        assert isinstance(start, int)
        assert isinstance(stop, int)
        #return [item.decode("utf8") for item in self.client.lrange(self.path(key), start, stop)]
        return self.client.lrange(self.path(key), start, stop)

    def llen(self, key):
        assert isinstance(key ,str)
        return self.client.llen(self.path(key))



    def path(self, *args):
        """ OVERRIDE THIS FUNCTION
        """

        raise NotImplementedError

