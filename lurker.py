import logging
import sys

from SinkNode import SinkNode
from SinkNode.Reader.SerialReader import SerialReader
from SinkNode.Reader.SocketReader import SocketReader
from SinkNode.Writer.LogFileWriter import LogFileWriter
from SinkNode.Formatter.CSVFormatter import CSVFormatter
from SinkNode.Writer.DweetWriter import DweetWriter

from settings import *

lurker_reader = SerialReader(SERIAL_PORT, BAUD_RATE, start_delimiter=ENTRY_START, stop_delimiter=ENTRY_END,
                             logger_level=logging.DEBUG)

motion_listener = SocketReader()

uploader = DweetWriter('lurker0', logger_level=logging.INFO)

file_logger = LogFileWriter('lurker.log', formatter=CSVFormatter(), writer_id='LurkerLog')

ingestor = SinkNode(logger_level=logging.INFO)
ingestor.add_reader(lurker_reader)
ingestor.add_reader(motion_listener)
ingestor.add_logger(file_logger)
ingestor.add_writer(uploader)

ingestor.start()

while True:
    try:
        continue

    except KeyboardInterrupt:
        ingestor.stop()
        sys.exit()


