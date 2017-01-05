# Russound Python API
Implements a Python API for selected commands to the Russound system using the RNET protocol predominantly developed to
provide Russound support within home-assistant.io.
The class is designed to maintain a connection to the Russound controller, and reads the state directly 
from the controller using RNET.  In principle supported models include the CAS44, CAA66, CAM6.6 and CAV6.6.
Although testing has only been done on CAA66 and CAV6.6.  Function to control Russound implemented are:

####For a zone:
* set_power
* set_volume
* set_source
* toggle_mute
* get_power
* get_volume
* get_source

####Controller level
* all_on_off

test_harness.py shows some examples of usage.