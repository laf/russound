"""
Russound CAV6.6 interface

Copyright (c) 2014 Neil Lathwood <https://github.com/laf/ http://www.lathwood.co.uk/>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.  Please see LICENSE.txt at the top level of
the source code distribution for details.

"""

import logging
import sys
import socket

_LOGGER = logging.getLogger(__name__)

class Russound:

    def __init__(self, host, port):
        """ Initialise Russound class """

        self._host = host
        self._port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """ Connect to the tcp gateway """

        try:
            self.sock.connect((self._host, self._port))
        except socket.error as msg:
            print("Couldn't connect to %s:%d - %s" % (self._host, self._port, msg))
            sys.exit(1)

    def set_power(self, controller, zone, power):
        """ Switch power on/off to a zone """

        event_id = '23'
        data = [controller, zone, power, event_id]
        data = self.format_data(data)
        self.send_data(data)

    def set_volume(self, controller, zone, volume):
        """ Set volume for zone to specific value """

        event_id = '21'
        hex_volume = int(volume)//2
        hex_volume = str(hex(hex_volume).lstrip("0x"))
        data = [controller, zone, hex_volume, event_id]
        data = self.format_data(data)
        self.send_data(data)

    def set_source(self, controller, zone, source):
        """ Set source for a zone """

        event_id = '3E'
        data = [controller, zone, source, event_id]
        data = self.format_data(data)
        self.send_data(data)

    def format_data(self, data):
        """ Format the data for sending """

        static_data = ['F0', 'CTRL', '00', '7F', '00', '00', '70', '05', '02', '02', '00', '00', 'F1', 'EID', '00', 'ACT', '00', 'ZONE', '00', '01']
        static_data[1] = '{0:02x}'.format(int(data[0],16))
        static_data[17] = '{0:02x}'.format(int(data[1],16))
        static_data[15] = '{0:02x}'.format(int(data[2],16))
        static_data[13] = '{0:02x}'.format(int(data[3],16))
        return(self.calc_checksum(static_data))

    def send_data(self, data):
        """ Send data to connected gateway """

        for item in data:
            data = bytes.fromhex(str(item))
            self.sock.send(data)

    def calc_checksum(self, data):
        """ Calculate the checksum we need """

        output = 0
        length = len(data)
        for value in data:
            output = output + int(value, 16)

        output = output + length
        checksum = hex(output & int('0x007F', 16)).lstrip("0x")
        checksum = int(checksum)
        data.append(checksum)
        data.append('F7')
        print(data)
        return data

    def __exit__(self):
        """ Close connection to gateway """
        try:
            self.sock.close()
        except socket.error as msg:
            print("Couldn't disconnect")
