"""
Russound CAV6.6 interface

Copyright (c) 2014 Neil Lathwood <https://github.com/laf/ http://www.lathwood.co.uk/>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.  Please see LICENSE.txt at the top level of
the source code distribution for details.

The Russound RNET protocol is documented in cav6.6_rnet_protocol_v1.01.00.pdf, which is stored in the source code repo.
"""

import logging
import time
import socket

_LOGGER = logging.getLogger(__name__)


class Russound:

    def __init__(self, host, port):
        """ Initialise Russound class """

        self._host = host
        self._port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, keypad=None):
        """ Connect to the tcp gateway
        Allow for this function to be keypad agnostic
        If keypad value is omitted, then set it to the hex value of 70 which is the recommended value for an external
        device controlling the system (top of pg 3 of cav6.6_rnet_protocol_v1.01.00.pdf). (In fact I don't know under
        what circumstances we would actually want to pass a keypadID at all).
        """

        if keypad is None:
            keypad = '70'
        try:
            self.sock.connect((self._host, self._port))
            self._keypad = keypad
            _LOGGER.info("Successfully connected to Russound on %s:%s", self._host, self._port)
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
        """ Parse to hex
        :param value: value to be converted to hex
        :param zc: flag that determines whether the value should be 0 based.
        :return: hex value returned
        """
        value = int(value)
        # Controller ID and Zone Id must be passed in as 1 based,
        # but they need to be 0 based for Russound, hence subtract 1.
        if zc:
            value -= 1
        value = hex(value).lstrip("0x")
        if not value:
            value = '0'
        return value

    def set_power(self, controller, zone, power):
        """ Switch power on/off to a zone
        :param controller: Russound Controller ID. For systems with one controller this should be a value of 1.
        :param zone: The zone to be controlled. Expect a 1 based number.
        :param power: 0 = off, 1 = on
        """

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
        self.receive_data()  # Clear buffer in case there is any response data (ensures correct results on future reads)
        _LOGGER.info("Russound on controller %s and zone %s power set to %s.", controller, zone, power)

    def set_volume(self, controller, zone, volume):
        """ Set volume for zone to specific value.
        Divide the volume by 2 to translate to a range (0..50) as expected by Russound (Even thought the
        keypads show 0..100).
        """

        _LOGGER.info("Russound volume on controller %s and zone %s set to level %s.", controller, zone, volume)
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
        self.receive_data()  # Clear buffer in case there is any response data (ensures correct results on future reads)

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
        self.receive_data()  # Clear buffer in case there is any response data (ensures correct results on future reads)

    def all_on_off(self, power):
        """ Turn all zones on or off
        Note that the all on function is not supported by the Russound CAA66, although it does support the all off.
        On and off are supported by the CAV6.6.
        """

        request = "F0 7F 00 7F 00 00 kk 05 02 02 00 00 F1 22 00 00 ## 00 00 01"
        data = request.split()
        data[6] = self._keypad
        data[17] = power
        data = self.calc_checksum(data)
        self.send_data(data)
        self.receive_data()  # Clear buffer in case there is any response data (ensures correct results on future reads)

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
        self.receive_data()  # Clear buffer in case there is any response data (ensures correct results on future reads)

    def get_power(self, controller, zone):
        """ Get source power status
        :return: 0 power off, 1 power on
        """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F 00 00 kk 01 04 02 00 zz 06 00 00"
        data = request.split()
        data[1] = cc
        data[6] = self._keypad
        data[11] = zz
        data = self.calc_checksum(data)
        self.send_data(data)
        response = self.receive_data()  # Expected response is as per pg 23 of cav6.6_rnet_protocol_v1.01.00.pdf
        if len(response) == 23:  # Check that the response is the correct length
            power_state = response[20]
        else:
            power_state = None
            _LOGGER.warning("Error obtaining Russound power state for controller %s and zone %s.", controller, zone)
            _LOGGER.warning("Expected a response of length 23 and received %s.", response)
        return power_state

    def get_volume(self, controller, zone):
        """ Get zone volume status
        Note that Russound internally has a volume range (0..50).  The expected result of this function is 0 to 100.
        Hence we multiply the result by 2.
        :return: volume level (0..100).
        """

        cc = self.parse_to_hex(controller, True)
        zz = self.parse_to_hex(zone, True)
        request = "F0 cc 00 7F 00 00 kk 01 04 02 00 zz 01 00 00"
        data = request.split()
        data[1] = cc
        data[6] = self._keypad
        data[11] = zz
        data = self.calc_checksum(data)
        self.send_data(data)
        response = self.receive_data()
        volume_level = response[20] * 2
        return volume_level

    def send_data(self, data):
        """ Send data to connected gateway """

        for item in data:
            data = bytes.fromhex(str(item.zfill(2)))
            self.sock.send(data)

    def receive_data(self, timeout=0.1):
        """ Receive data from connected gateway
        (Initially the timeout was set to 2s.  This resulted in long delays when this method was called.
        Through trial and error a value of 0.1s works well in my case.  But there may be a better way of handling this
        beyond hard-coding this to an artbitrary number?
        """

        self.sock.setblocking(0)
     
        # total data partwise in an array
        total_data=[];
        data='';
     
        # beginning time
        begin=time.time()
        while 1:
            # if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
         
            # if you got no data at all, wait a little longer, twice the timeout
            elif time.time()-begin > timeout * 2:
                break
         
            # recv something
            try:
                data = self.sock.recv(8192)
                if data:
                    total_data.append(data)
                    # change the beginning time for measurement
                    begin=time.time()
                else:
                    # sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
     
        # join all parts to make final string
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
            _LOGGER.info("Closed connection to Russound on %s:%s", self._host, self._port)
        except socket.error as msg:
            _LOGGER.error("Couldn't disconnect")
