__author__ = 'Leenix'

import serial
import httplib
import urllib
import logging
from threading import Thread
import json
from Queue import Queue


class Lurker(object):
    """Model for the Lurker sensor platform.

    The connected lurker acts as a sink node for the sensor network.
    Remote data is pre-processed into JSON format before being sent
    over serial. The Lurker module does not possess a real-time
    clock, so data incoming data will be processed whenever received
    by the sink node.

    Args:
        port: The name of the serial port on which the Lurker is connected
            e.g. COM1 or ttyUSB0

    Attributes:
        ser: serial communications manager
        reading_thread: reading thread for serial communications
        is_reading: Flag to indicate whether the reading thread is on or not
    """

    ENTRY_START = "#"
    ENTRY_END = "$"

    def __init__(self, port):
        """Initialise new Lurker device
        """
        self.received_entries = Queue()
        self.port = port
        self.ser = serial.Serial()
        self.reading_thread = Thread(target=self.read_loop)
        self.is_reading = False

    def connect(self, baud_rate=57600):
        """Connect to the Lurker sink over serial

        Args:
            baud_rate: The baud rate for the serial interface

        """
        self.ser.setBaudrate(baud_rate)
        self.ser.setPort(self.port)

        try:
            self.ser.open()
            logging.info('Connected to Lurker')
        except serial.SerialException:
            logging.error('Error opening serial port')

    def disconnect(self):
        """Disconnect from the Lurker sink

        Does nothing if no serial connection is open
        """

        if self.ser.isOpen():
            self.ser.close()
            logging.info("Disconnected")

    def start_logging(self):
        """Start receiving data from the Lurker sink

        The Lurker serial port is monitored in a separate thread.
        Once an entire entry has been received, the entry is processed into
        dictionary format.
        """

        if not self.reading_thread.isAlive() and self.ser.isOpen():
            self.reading_thread.setDaemon(True)
            self.reading_thread.start()
            self.is_reading = True
            logging.info("Listening thread started")

        else:
            self.is_reading = False

    def read_loop(self):
        """
        """
        logging.debug("Entered read loop")
        while self.is_reading:

            entry_line = ""

            c = self.ser.read()
            while c != Lurker.ENTRY_END:
                entry_line += c
                c = self.ser.read()

            logging.debug(entry_line)
            start_index = entry_line.find(Lurker.ENTRY_START)

            # Cut out anything before the start delimiter
            if start_index >= 0:
                entry_line = entry_line[start_index + 1:]
                logging.debug("Pre-processed: " + entry_line)
                try:
                    entry = json.loads(entry_line)
                    logging.debug(entry)
                    self.received_entries.put(entry)
                except ValueError:
                    logging.error("Non-JSON data")

    def stop_logging(self):
        """Stop listening on the Lurker

        Does nothing if the listening thread is not running
        """

        if self.is_reading:
            self.is_reading = False

        self.received_entries.join()


class TooManyFields(ValueError):
    pass


class LurkerProcessor(object):
    KEY_MAP = {
        "air_temp": "field1",
        "surface_temp": "field2",
        "humidity": "field3",
        "illuminance": "field4",
        "noise_level": "field5",
        "motion": "field6"
    }

    CHANNEL_MAP = {
        "lurker1": "JLLN86V2D0X1ZMDU",
        "lurker2": "JLLN86V2D0X1ZMDU"
    }

    @staticmethod
    def process_entry(entry):
        """Process an incoming JSON entry into thingspeak format.

        The mapping is determined by the sensor_data_keys map
        for translating type names into field names.

        The CHANNEL_MAP list gives each ID the proper API key
        so the data is entered into the correct channel (assuming
        each unit has its own channel.

        :param entry: JSON format of sensor data = {
                        "id": unit_id,
                        "temperature": temp_data,
                        "humidity": humidity_data,...
                        }

        :return: JSON data in Thingspeak format = {
                        "key": API_KEY
                        "field1": field1_data
                        "field2": field2_data...
                        }
        """

        output = {}

        # Each entry must have an ID to be valid so we know where it's going
        if "id" in entry and entry["id"] in LurkerProcessor.CHANNEL_MAP:
            channel_key = LurkerProcessor.CHANNEL_MAP[entry["id"]]
            output["key"] = channel_key

            # Map the rest of the data into fields
            # Extra data will be ignored
            for k in entry:
                if k in LurkerProcessor.KEY_MAP:
                    new_key = LurkerProcessor.KEY_MAP[k]
                    output[new_key] = entry[k]

        return output

    def process_loop(self):
        """

        :return:
        """
        while self.is_reading:
            entry = self.received_entries.get()
            processed_entry = self.processor.process_entry(entry)
            logging.debug("Processed: " + processed_entry)
            # upload shit
            self.received_entries.task_done()

    def non_null_values(**kwargs):
        return [(k,v) for (k,v) in kwargs.iteritems() if v != None]


class ThingspeakChannel(object):
    HEADERS = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    def __init__(self, write_key, read_key=None, server_address="api.thingspeak.com:80"):
        """ Create a new thingspeak channel uploader thing

        :param write_key: API_KEY for writing to the thingspeak server
        :param read_key: API_KEY for reading from the thingspeak server
        :param server_address: Server address for the thingspeak server
                could be custom I guess
        """
        self.write_key = write_key
        self.read_key = read_key
        self.server_address = server_address

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
            params = urllib.urlencode([('key',read_key)])
            conn.request("GET", path, params, ThingspeakChannel.HEADERS)
            response = conn.getresponse()
            return response


def main():
    logging.basicConfig(level=logging.DEBUG)
    lurker = Lurker("COM7")
    lurker.connect()
    lurker.start_logging()

    while True:
        new_entry = lurker.received_entries.get()
        processed_entry = LurkerProcessor.process_entry(new_entry)
        logging.debug("Processed entry: " + str(processed_entry))
        ThingspeakChannel.update(processed_entry)
        logging.info("Entry uploaded")
        lurker.received_entries.task_done()


if __name__ == '__main__':
    main()
