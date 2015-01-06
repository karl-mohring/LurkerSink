LurkerSink
==========

Automatic uploading of sensor data from a connected Lurker to Thingspeak.

These instructions will be for linux implementation. The Python package manager behaves a little differently in Windows, but it's not too hard to figure out.


Install the pre-requisites
==========================

In a bash terminal, type:

	sudo apt-get update
	sudo apt-get install python-pip git cron
	sudo pip install pyserial simplejson

Download the script
===================

Download the Lurker Sink script from Github using the following commands:

	cd ~
	git clone https://github.com/leenix/LurkerSink
	
Configuration
=============

Settings
--------
The settings.py file contains some basic mapping options for a Thingspeak channel.

* The _CHANNEL_MAP_ contains mapping between different unit id's (e.g. "lurker1") and channels, which are specified by their API key.

* Data fields are mapped to Thingspeak fields in the _KEY_MAP_

* Finally, the _SERIAL_PORT_ option gives the default port for the Lurker

Both the channel and field/key mapping need to match the settings on your Thingspeak channel.

Thingspeak
----------
Go to your Thingspeak channel dashboard. 

- The _Channel Settings_ tab contains the field details. The _KEY_MAP_ in the settings file should reflect the fields are set to on this screen.

- The _API Keys_ tab has the __Write API Key__, which needs to be copied into the CHANNEL_MAP for each channel ID.


Automatic start using Cron
==========================
Cron is a basic scheduling tool that can be used to set up timed events. A Cron Table is checked every minute to determine which scripts need to be run.

1) In a bash terminal, type:

	crontab -e
	
This will open up an editing window for the Cron Table, which is the scheduling script. The script will be blank if Cron has not be used before.

2) At the end of the script (after the # lines), type the following:

@reboot /usr/bin/python <location of LurkerSink script>
This script will run whenever the Pi/computer is turned on. Other time frames can be specified by following this guide: http://www.thegeekstuff.com/2011/07/cron-every-5-minutes/

3) Hit 'Ctrl+X' to close the Cron Table. Don't forget to save. Cron scripts become active as soon as the table has been saved.
