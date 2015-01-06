__author__ = 'Leenix'

import unittest
import logging
import serial
import time
import json

from lurker import Lurker, ThingspeakChannel
from settings import *

TEST_PORT = "loop://"
TEST_ENTRY = {
    "id": "lurker1",
    "air_temp": 12.34,
    "surface_temp": 23.45,
    "humidity": 34.56,
    "illuminance": 456,
    "noise_level": 567,
    "motion": "yes"
}


class LurkerTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.test_lurker = Lurker(TEST_PORT)
        self.test_lurker.ser = serial.serial_for_url(TEST_PORT)

    def test_create(self):
        """ Ensure the lurker instantiates correctly

        Fails:
            If any errors occur during lurker creation
        """
        self.setUp()
        self.assertIsInstance(self.test_lurker, Lurker)

    def test_process_entry(self):
        """ Test the mapping of incoming entries to thingspeak format

        Fails:
            Key has not been correctly mapped (key = API_KEY_1)
            Field has not been mapped correctly ( air temp data == field1 data)
        """
        processed_entry = Lurker.map_entry(TEST_ENTRY)
        print(processed_entry)
        self.assertEqual(processed_entry["key"],
                         CHANNEL_MAP["lurker1"],
                         "Bad key map")

        self.assertEqual(TEST_ENTRY["air_temp"],
                         processed_entry["field1"],
                         "Bad value map")

        self.assertNotEqual(TEST_ENTRY["humidity"],
                            processed_entry["field1"],
                            "Bad mapping order")

    def test_connect(self):
        """ Show that the serial module is set up correctly

        The testing module uses a local loop to open a virtual serial port

        Fails:
            Serial port not open after connection attempt
        """
        self.assertTrue(self.test_lurker.ser.isOpen())

    def test_disconnect(self):
        """ Close the test serial port

        Fails:
            Serial connection is still open after disconnecting
        """
        self.test_lurker.disconnect()
        self.assertFalse(self.test_lurker.ser.isOpen())

    def test_reading_loop(self):
        """ Check that the reading thread is running

        Fails:
            If the read thread does not start
        """
        self.test_lurker.start_logging()
        self.assertTrue(self.test_lurker.is_reading)
        time.sleep(1)

    def test_queueing(self):
        """ Check that an incoming packet is being processed

        """
        self.test_lurker.start_logging()
        self.assertTrue(self.test_lurker.received_entries.empty())
        self.test_lurker.ser.write("#{\"id\":\"lurker1\",\"temperature\":24.56}$")
        time.sleep(1)
        self.assertFalse(self.test_lurker.received_entries.empty())

    def test_queue_non_json(self):
        """ Ensure non-JSON format inputs are not entered into the queue.

        Fails:
            Queue is not empty before test
            Incorrect string is entered into queue
        """
        self.test_lurker.start_logging()
        self.assertTrue(self.test_lurker.received_entries.empty())
        self.test_lurker.ser.write("#NOT JSON$")
        self.assertTrue(self.test_lurker.received_entries.empty())

    def test_upload(self):
        new_entry = "{\"id\": \"lurker1\", \"motion\": 1}"
        formatted_entry = json.loads(new_entry)
        processed_entry = Lurker.map_entry(formatted_entry)
        logging.debug("Processed entry: " + str(processed_entry))
        ThingspeakChannel.update(processed_entry)
        logging.info("Entry uploaded")


def main():
    unittest.main()


if __name__ == '__main__':
    unittest.main()
