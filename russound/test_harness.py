""" Used for adhoc testing.  in time can create formal tests. """

import logging
import russound
import time

IP_ADDRESS = '192.168.1.72'
PORT = 9001
logging.basicConfig(filename='russound_debugging.log', level=logging.DEBUG,
                    format='%(asctime)s:%(name)s:%(levelname)s:%(funcName)s():%(message)s')
_LOGGER = logging.getLogger(__name__)

def test1():
    x = russound.Russound(IP_ADDRESS, PORT)
    x.connect()
    zone = '1'
    print("Turn off zone", zone)
    x.set_power('1', zone, '0')
    print("Power status zone", zone, "=", x.get_power('1', zone))

    print("Turn on zone", zone)
    x.set_power('1', zone, '1')
    print("Power status zone", zone, "=", x.get_power('1', zone))

    print("Source on zone", zone, "is", x.get_source('1',zone))
    x.set_source('1', zone, '0')
    print("Source on zone", zone, "is", x.get_source('1',zone))

    print("Volume on zone", zone, "is", x.get_volume('1',zone))
    x.set_volume('1', zone, 20)
    print("Volume on zone", zone, "is", x.get_volume('1',zone))


def test2():
    """ Used this approach to determine what responses and when are turned from Russound """
    x = russound.Russound(IP_ADDRESS, PORT)
    x.connect()
    controller = '1'
    zone = '1'
    sequence = []
    for i in range(0,51):
        sequence.append(None)

    #sequence[5] = ('set_power_off', x.create_message("F0 @cc 00 7F 00 00 @kk 05 02 02 00 00 F1 23 00 @pr 00 @zz 00 01", controller, zone, 0))
    sequence[5] = ('get_power', x.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 06 00 00", controller, zone))
    sequence[10] = ('get_source', x.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 02 00 00", controller, zone))
    sequence[15] = ('get_source', x.create_send_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 01 00 00", controller, zone))
    #sequence[15] = ('set_power_on', x.create_message("F0 @cc 00 7F 00 00 @kk 05 02 02 00 00 F1 23 00 @pr 00 @zz 00 01", controller, zone, 1))
    #sequence[20] = ('get_power', x.create_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 06 00 00", controller, zone))
    #sequence[50] = ('get_power', x.create_message("F0 @cc 00 7F 00 00 @kk 01 04 02 00 @zz 06 00 00", controller, zone))

    t = 0
    for item in sequence:
        if item is not None:
            print(round(t, 1), item[0], "...")
            x.send_data(item[1])
        else:
            response = x.receive_data0()
            print(round(t, 1), "Receiving message...", list(response))
            print(x.get_received_messages(response))
            #if len(response) > 0:
            #    print(response)
        time.sleep(0.1)
        t += 0.1



def test3():
    """ All zones on, change sound and then all off """

    x = russound.Russound(IP_ADDRESS, PORT)
    x.connect()
    x.is_connected()
    for zone in range(1, 5):
        x.set_power('1', zone, '1')
        print("Power status zone", zone, "is", x.get_power('1', zone))

    for zone in range(1,5):
        x.set_volume('1', zone, 34)
        print("Volume on zone", zone, "is", x.get_volume('1', zone))

    time.sleep(5)
    for zone in range(1, 5):
        x.set_power('1', zone, '0')


def test4():
    x = russound.Russound(IP_ADDRESS, PORT)
    x.connect()
    x.is_connected()
    zone = '1'

    print("For zone 1, read power status, turn zone on and read volume and source")
    _LOGGER.debug("Zone %s power status=%s", zone, x.get_power('1', zone))
    x.set_power('1', zone, '1')
    _LOGGER.debug("Zone %s power status=%s", zone, x.get_power('1', zone))
    _LOGGER.debug("Zone %s source=%s", zone, x.get_source('1',zone))
    _LOGGER.debug("Zone %s volume=%s", zone, x.get_volume('1',zone))

    print("Set volume to 35 and source to 2nd source")
    x.set_volume('1', zone, 35)
    x.set_source('1', zone, 1)

    print("Read the source and volume levels from the controller")
    _LOGGER.debug("Zone %s source=%s", zone, x.get_source('1',zone))
    _LOGGER.debug("Zone %s volume=%s", zone, x.get_volume('1',zone))

    time.sleep(2)
    x.set_power('1', zone, '0')
    _LOGGER.debug("Zone %s source=%s", zone, x.get_source('1',zone))


#Run test 4...
test4()