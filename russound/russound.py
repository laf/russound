"""
Russound RNT interface (used by models CAS44, CAA66, CAM6.6, CAV6.6)

Copyright (c) 2014 Neil Lathwood <https://github.com/laf/ http://www.lathwood.co.uk/>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.  Please see LICENSE.txt at the top level of
the source code distribution for details.

The Russound RNET protocol is documented in cav6.6_rnet_protocol_v1.01.00.pdf, and russound-rs-232-V01_00_01.pdf
which are stored in the source code repo.
"""

import logging
import time
import socket

_LOGGER = logging.getLogger(__name__)
# Recommendation is that this should be at leat 100ms delay to ensure subsequent commands
# are processed correctly (pg 35 on russound-rs-232-V01_00_01.pdf).
COMMAND_DELAY = 0.1
KEYPAD_CODE = '70'  # For an external system this is the required value (pg 28 of cav6.6_rnet_protocol_v1.01.00.pdf)


class Russound:
    def __init__(self, host, port):
        """ Initialise Russound class """

        self._host = host
        self._port = int(port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """ Connect to the tcp gateway
        Allow for this function to be keypad agnostic
        If keypad value is omitted, then set it to the hex value of 70 which is the recommended value for an external
        device controlling the system (top of pg 3 of cav6.6_rnet_protocol_v1.01.00.pdf). (In fact I don't know under
        what circumstances we would actually want to pass a keypadID at all).
        """

        try:
            self.sock.connect((self._host, self._port))
            _LOGGER.info("Successfully connected to Russound on %s:%s", self._host, self._port)
            return True
        except socket.error as msg:
            _LOGGER.error("Error trying to connect to Russound controller.")
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

    def set_power(self, controller, zone, power):
        """ Switch power on/off to a zone
        :param controller: Russound Controller ID. For systems with one controller this should be a value of 1.
        :param zone: The zone to be controlled. Expect a 1 based number.
        :param power: 0 = off, 1 = on
        """

        send_msg = self.create_send_message("F0 @cc 00 7F 00 00 @kk 05 02 02 00 00 F1 23 00 @pr 00 @zz 00 01",
                                            controller, zone, power)
        self.send_data(send_msg)
        self.receive_data()  # Clear response buffer
        _LOGGER.info("Russound on controller %s and zone %s power set to %s.", controller, zone, power)

    def set_volume(self, controller, zone, volume):
        """ Set volume for zone to specific value.
        Divide the volume by 2 to translate to a range (0..50) as expected by Russound (Even thought the
        keypads show 0..100).
        """

        _LOGGER.info("Russound volume on controller %s and zone %s set to level %s.", controller, zone, volume)
        send_msg = self.create_send_message("F0 @cc 00 7F 00 00 @kk 05 02 02 00 00 F1 21 00 @pr 00 @zz 00 01",
                                            controller, zone, volume//2)
        self.send_data(send_msg)
        self.receive_data()  # Clear response buffer

    def set_source(self, controller, zone, source):
        """ Set source for a zone - 0 based value for source """

        send_msg = self.create_send_message("F0 @cc 00 7F 00 @zz @kk 05 02 00 00 00 F1 3E 00 00 00 @pr 00 01",
                                            controller, zone, source)
        self.send_data(send_msg)
        self.receive_data()  # Clear response buffer in case there is any response data (ensures correct results on future reads)

    def all_on_off(self, power):
        """ Turn all zones on or off
        Note that the all on function is not supported by the Russound CAA66, although it does support the all off.
        On and off are supported by the CAV6.6.
        Note: Not tested (acambitsis)
        """

        send_msg = self.create_send_message("F0 7F 00 7F 00 00 @kk 05 02 02 00 00 F1 22 00 00 @pr 00 00 01",
                                            None, None, power)
        self.send_data(send_msg)
        self.receive_data()  # Clear response buffer

    def toggle_mute(self, controller, zone):
        """ Toggle mute on/off for a zone
        Note: Not tested (acambitsis) """

        send_msg = self.create_send_message("F0 @cc 00 7F 00 @zz @kk 05 02 02 00 00 F1 40 00 00 00 0D 00 01",
                                            controller, zone)
        self.send_data(send_msg)
        self.receive_data()  # Clear response buffer

    def get_power(self, controller, zone):
        """ Get source power status
        :return: 0 power off, 1 power on
        """

        # Define the signature for a response message, used later to find the correct response from the controller.
        # FF is the hex we use to signify bytes that need to be ignored when comparing to response message.
        resp_msg_signature = self.create_response_signature(
            "F0 00 00 70 00 00 7F 00 00 04 02 00 @zz 06 00 00 01 00 01 00 FF FF F7", zone)

        send_msg = self.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 06 00 00", controller, zone)

        self.send_data(send_msg)
        response_stream = self.receive_data()  # Expected response is as per pg 23 of cav6.6_rnet_protocol_v1.01.00.pdf
        matching_message = self.find_matching_message(response_stream, resp_msg_signature)
        if matching_message is not None:  # Check that the response is the correct length
            power_state = matching_message[20]
        else:
            power_state = None
            _LOGGER.warning("Error obtaining Russound power state for controller %s and zone %s.", controller, zone)
            _LOGGER.warning("Did not receive expected response message from Russound controller.")
        return power_state

    def get_volume(self, controller, zone):
        """ Get zone volume status
        Note that Russound internally has a volume range (0..50).  The expected result of this function is 0 to 100.
        Hence we multiply the result by 2.
        :return: volume level (0..100).
        """

        # Define the signature for a response message, used later to find the correct response from the controller.
        # FF is the hex we use to signify bytes that need to be ignored when comparing to response message.
        resp_msg_signature = self.create_response_signature(
            "F0 00 00 70 00 00 7F 00 00 04 02 00 @zz 01 00 00 01 00 01 00 FF FF F7", zone)

        send_msg = self.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 01 00 00", controller, zone)
        self.send_data(send_msg)
        response_stream = self.receive_data()
        matching_message = self.find_matching_message(response_stream, resp_msg_signature)
        if matching_message is not None:
            volume_level = matching_message[20] * 2  # Note: Referencing a single value from a byte array converts to base10 automatically
        else:
            volume_level = None
            _LOGGER.warning("Error obtaining Russound volume for controller %s and zone %s.", controller, zone)
            _LOGGER.warning("Did not receive expected response message from Russound controller.")
        return volume_level

    def get_source(self, controller, zone):
        """ Get the currently selected source for the zone
        :return: a zero based index of the source
        """

        # Define the signature for a response message, used later to find the correct response from the controller.
        # FF is the hex we use to signify bytes that need to be ignored when comparing to response message.
        resp_msg_signature = self.create_response_signature(
            "F0 00 00 70 00 00 7F 00 00 04 02 00 @zz 02 00 00 01 00 01 00 FF FF F7", zone)
        send_msg = self.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 02 00 00", controller, zone)
        data = self.calc_checksum(send_msg)
        self.send_data(data)
        response_stream = self.receive_data()
        matching_message = self.find_matching_message(response_stream, resp_msg_signature)
        if matching_message is not None:
            selected_source = matching_message[20]
        else:
            selected_source = None
            _LOGGER.warning("Error obtaining Russound source for controller %s and zone %s.", controller, zone)
            _LOGGER.warning("Did not receive expected response message from Russound controller.")
        return selected_source

    def create_send_message(self, string_message, controller, zone=None, parameter=None):
        """ Creates a message from a string, substituting the necessary parameters,
        that is ready to send to the socket """

        cc = hex(int(controller)-1).replace('0x', '')  # RNET requires controller value to be zero based
        if zone is not None:
            zz = hex(int(zone)-1).replace('0x', '')  # RNET requires zone value to be zero based
        else:
            zz = ''
        if parameter is not None:
            pr = hex(int(parameter)).replace('0x', '')
        else:
            pr = ''

        string_message = string_message.replace('@cc', cc)  # Replace controller parameter
        string_message = string_message.replace('@zz', zz)  # Replace zone parameter
        string_message = string_message.replace('@kk', KEYPAD_CODE)  # Replace keypad parameter
        string_message = string_message.replace('@pr', pr)  # Replace specific parameter to message

        # Split message into an array for each "byte" and add the checksum and end of message bytes
        send_msg = string_message.split()
        send_msg = self.calc_checksum(send_msg)
        return send_msg

    def create_response_signature(self, string_message, zone):
        """ basic helper function to keep code clean for defining a response message signature """

        if zone is not None:
            zz = hex(int(zone)-1).replace('0x', '')  # RNET requires zone value to be zero based
        string_message = string_message.replace('@zz', zz)  # Replace zone parameter
        return string_message

    def send_data(self, data, delay=COMMAND_DELAY):
        """ Send data to connected gateway """

        time.sleep(delay)  # Insert recommended delay to ensure command is processed correctly
        for item in data:
            data = bytes.fromhex(str(item.zfill(2)))
            try:
                self.sock.send(data)
            except ConnectionResetError as msg:
                _LOGGER.error("Error trying to connect to Russound controller. "
                        "Check that no other device or system is using the port that you are trying to connect to. "
                        "Try resetting the bridge you are using to connect.")
                _LOGGER.error(msg)

    def receive_data(self, delay=COMMAND_DELAY, no_of_socket_reads=1):
        """ Receive data from connected gateway
        Based on testing, 100ms is enough to provide the full response message.  It is unlikely the this will be
        influenced heavily by the environment, since message a very short and typical operation is in a LAN context.
        Therefore by default we wait for 100ms before processing the recevie (as recommended) and make one read attempt.
        """

        time.sleep(delay)  # Insert recommended delay to ensure command is processed correctly
        self.sock.setblocking(0)  # Needed to prevent request for waiting indefinitely

        data = b''
        for i in range(0, no_of_socket_reads):
            try:
                # Receive whatever has been sent
                data += self.sock.recv(8192)
                # Check that the last character represent end of message
            except BlockingIOError:  # Expected outcome if there is not data
                pass
            except ConnectionResetError as msg:
                _LOGGER.error("Error trying to connect to Russound controller. "
                        "Check that no other device or system is using the port that you are tryiong to connect to. "
                        "Try resetting the bridge you are using to connect.")
                _LOGGER.error(msg)
            time.sleep(delay)  # Wait before reading again
        _LOGGER.debug(data)
        return data

    def find_matching_message(self, data_stream, msg_signature):
        """ Takes the stream of bytes received and looks for a message that matches the signature
        of the expected response """

        matched_message = None  # The message that will be returned if it matches the signature
        returned_messages = self.get_received_messages(data_stream)  # get list of messages from response stream
        msg_signature = msg_signature.split()  # Split into list
        # convert to bytearray in order to be able to compare with the messages list which contains bytearrays
        msg_signature = bytearray(int(x, 16) for x in msg_signature)
        # loop through each message returned from Russound
        for returned_message in returned_messages:
            matched_message = None  # Assume no match
            if len(msg_signature) == len(returned_message):  # Eliminate obvious mistmatch if msgs not same length
                matched_message = returned_message  # Assume its a match
                #  loop through each byte and see if the are different
                for i in range(0, len(returned_message)):
                    # Only test if bytes are the same if signature msg byte is not 255 (our ignore value)
                    # Note when returning a single byte a list it evalautes to an integer
                    if msg_signature[i] != 255 and msg_signature[i] != returned_message[i]:
                        matched_message = None  # No match found
                        break
                if matched_message is not None:  # Loop complete.  If match found break out of out loop.
                    break
        _LOGGER.debug(matched_message)
        return matched_message

    def get_received_messages(self, data_stream):
        """ Break received stream into a list of RNET messages, based on start and end characters """

        messages = []  # List of messages that will be returned
        start_index = -1
        end_index = -1
        for i in range(0, len(data_stream)):
            if data_stream[i] == 240:  # Start character (F0)
                start_index = i
            if data_stream[i] == 247:  # End character (F7)
                end_index = i
                if start_index > -1:  # Start and end have been found - therefore extract a full message
                    message = data_stream[start_index:end_index + 1]
                    start_index = -1
                    messages.append(message)
        _LOGGER.debug(messages)
        return messages

    def calc_checksum(self, data):
        """ Calculate the checksum we need """

        output = 0
        length = len(data)
        for value in data:
            output += int(value, 16)

        output += length
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
