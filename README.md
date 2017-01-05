# Russound Python API
Implements a Python API for selected commands to the Russound system using the RNET protocol predominantly developed to
provide Russound support within home-assistant.io.
The class is designed to maintain a connection to the Russound controller, and reads the state directly 
from the controller using RNET.  In principle supported models include the CAS44, CAA66, CAM6.6 and CAV6.6.
Although testing has only been done on CAA66 and CAV6.6.