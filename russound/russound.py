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
import time
import socket

_LOGGER = logging.getLogger(__name__)

class Russound:

    def __init__(self, host, port):
        """ Initialise Russound class """

        self._host = host
        self._port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, keypad):
        """ Connect to the tcp gateway """

        try:
            self.sock.connect((self._host, self._port))
            self._keypad = keypad
        except socket.error as msg:
            _LOGGER.error(msg)
            return False

    def is_connected(self):
        """ Check we are connected """

        try:
            if self.sock.getpeername():
                return True
            else:
                return False
        except:
            return False

    def parse_to_hex(self, value, zc=None):
        """ Parse to hex """

        value = int(value)
        if zc:
            value = value-1
        value = hex(value).lstrip("0x")
        if not value:
            value = '0'
        return(value)

    def set_power(self, controller, zone, power):
        """ Switch power on/off to a zone """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F cc 00 kk 05 02 02 00 00 F1 23 00 ## 00 zz 00 01"
        data = request.split()
        data[1] = cc
        data[4] = cc
        data[6] = self._keypad
        data[15] = power
        data[17] = zz
        data = self.calc_checksum(data) 
        self.send_data(data)

    def set_volume(self, controller, zone, volume):
        """ Set volume for zone to specific value """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F cc 00 kk 05 02 02 00 00 F1 21 00 ## 00 zz 00 01"
        volume = int(volume)//2
        volume = self.parse_to_hex(volume)
        data = request.split()
        data[1] = cc
        data[4] = cc
        data[6] = self._keypad
        data[15] = volume
        data[17] = zz
        data = self.calc_checksum(data)
        self.send_data(data)

    def set_source(self, controller, zone, source):
        """ Set source for a zone """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        source = self.parse_to_hex(source, True)
        request = "F0 cc 00 7F 00 zz kk 05 02 00 00 00 F1 3E 00 00 00 ## 00 01"        
        data = request.split()
        data[1] = cc
        data[5] = zz
        data[6] = self._keypad
        data[17] = source
        data = self.calc_checksum(data)
        self.send_data(data)

    def all_on_off(self):
        """ Turn all zones on or off """

        request = "F0 7F 00 7F 00 00 kk 05 02 02 00 00 F1 22 00 00 ## 00 00 01"
        data = request.split()
        data[6] = self._keypad
        data[17] = power
        data = self.calc_checksum(data)
        self.send_data(data)

    def toggle_mute(self, controller, zone):
        """ Toggle mute on/off for a zone """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F 00 zz kk 05 02 02 00 00 F1 40 00 00 00 0D 00 01"
        data = request.split()
        data[1] = cc
        data[5] = zz
        data[6] = self._keypad
        data = self.calc_checksum(data)
        self.send_data(data)

    def get_power(self, controller, zone):
        """ Get source power status """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F 00 00 kk 01 04 02 00 zz 06 00 00"
        data = request.split()
        data[1] = cc
        data[6] = self._keypad
        data[11] = zz
        data = self.calc_checksum(data)
        self.send_data(data)

    def send_data(self, data):
        """ Send data to connected gateway """

        for item in data:
            data = bytes.fromhex(str(item.zfill(2)))
            self.sock.send(data)

    def receive_data(self, timeout=2):
        """ Receive data from connected gateway """

        self.sock.setblocking(0)
     
        #total data partwise in an array
        total_data=[];
        data='';
     
        #beginning time
        begin=time.time()
        while 1:
            #if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
         
            #if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout*2:
                break
         
            #recv something
            try:
                data = self.sock.recv(8192)
                if data:
                    total_data.append(data)
                    #change the beginning time for measurement
                    begin=time.time()
                else:
                    #sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
     
        #join all parts to make final string
        return b''.join(total_data)

    def calc_checksum(self, data):
        """ Calculate the checksum we need """

        output = 0
        length = len(data)
        for value in data:
            output = output + int(value, 16)

        output = output + length
        checksum = hex(output & int('0x007F', 16)).lstrip("0x")
        data.append(checksum)
        data.append('F7')
        return data

    def __exit__(self):
        """ Close connection to gateway """
        try:
            self.sock.close()
        except socket.error as msg:
            print("Couldn't disconnect")
