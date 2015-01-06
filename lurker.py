#!/usr/bin.env python
__author__ = 'Leenix'

import serial
from ThingspeakChannel import *
from settings import *
import logging
from threading import Thread
import json
from Queue import Queue
import time


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

    def __init__(self, port=SERIAL_PORT):
        """
        Initialise the sink for a connected Lurker module

        Args:
            port:   The serial port on which the Lurker is connected

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

        if not self.ser.isOpen():
            self.connect()

        if not self.reading_thread.isAlive() and self.ser.isOpen():
            self.reading_thread.setDaemon(True)
            self.reading_thread.start()
            self.is_reading = True
            logging.info("Listening thread started")

        else:
            self.is_reading = False

    def read_entry(self):
        """
        Read a data entry in from the Lurker over serial.
        ! Blocking method

        :return: Data entry in string format. Data packets should be in JSON string.
        """
        entry_line = ""

        c = self.ser.read()

        while c != Lurker.ENTRY_END:
            entry_line += c
            c = self.ser.read()
        logging.debug(entry_line)

        return entry_line

    @staticmethod
    def convert_entry_to_json(entry_line):
        """
        Convert a data entry string into JSON format
        The conversion strips out the start and end packet characters

        :param entry_line: Data string to be converted into JSON
        :return:    JSON object containing sensor data
        """
        entry = ""

        # Cut out anything before the start delimiter
        start_index = entry_line.find(Lurker.ENTRY_START)
        if start_index >= 0:
            entry_line = entry_line[start_index + 1:]
            logging.debug("Pre-processed: " + entry_line)

            # Attempt to convert the packet string into JSON format
            try:
                entry = json.loads(entry_line)
                logging.debug(entry)

                logging.info(entry)

            except ValueError:
                logging.error("Non-JSON data: %s", entry_line)

        return entry

    def read_loop(self):
        """
        Serial reading loop for the attached Lurker
        The read loop is called by the Lurker's reading thread
        """
        
        logging.debug("Entered read loop")
        while self.is_reading:
            entry_line = self.read_entry()
            processed_entry = Lurker.convert_entry_to_json(entry_line)
            self.received_entries.put(processed_entry)

    def stop_logging(self):
        """
        Stop listening on the Lurker
        Does nothing if the listening thread is not running
        """

        if self.is_reading:
            self.is_reading = False

        self.received_entries.join()

    @staticmethod
    def map_entry(entry):
        """Process an incoming JSON entry into thingspeak format.

        Field mapping can be found in the settings.py file in the following format:
        date field name: thingspeak field name

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
        if "id" in entry and entry["id"] in CHANNEL_MAP:
            channel_key = CHANNEL_MAP[entry["id"]]
            output["key"] = channel_key

            # Map the rest of the data into fields
            # Extra data will be ignored
            for k in entry:
                if k in KEY_MAP:
                    new_key = KEY_MAP[k]
                    output[new_key] = entry[k]

        return output


def main():
    logging.basicConfig(level=logging.INFO)
    lurker = Lurker()
    lurker.start_logging()

    try:
        while True:
            new_entry = lurker.received_entries.get()
            processed_entry = Lurker.map_entry(new_entry)
            logging.debug("Processed entry: " + str(processed_entry))
            ThingspeakChannel.update(processed_entry)
            logging.info("Entry uploaded")
            lurker.received_entries.task_done()
            time.sleep(15)

    except KeyboardInterrupt:
        logging.INFO("Keyboard Interrupt - Shutting down")




if __name__ == '__main__':
    main()
