__author__ = 'Leenix'

import urllib
import httplib


class ThingspeakChannel(object):
    """
    Thingspeak upload manager based on the thingspeak library by bergey
    """
    HEADERS = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    @staticmethod
    def update(entry):
        params = urllib.urlencode(entry)
        conn = httplib.HTTPConnection("api.thingspeak.com:80")
        conn.request("POST", "/update", params, ThingspeakChannel.HEADERS)
        response = conn.getresponse()
        conn.close()
        return response

    @staticmethod
    def fetch(server_address, read_key, format_):
            conn = httplib.HTTPConnection(server_address)
            path = "/channels/{0}/feed.{1}".format(read_key, format_)
            params = urllib.urlencode([('key', read_key)])
            conn.request("GET", path, params, ThingspeakChannel.HEADERS)
            response = conn.getresponse()
            return response