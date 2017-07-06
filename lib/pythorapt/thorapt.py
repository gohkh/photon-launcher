"""
todo:
- make errors more specific
- look at active_channels and get_channel methods
- use less if statements!! ie make is nicer. shorter. more pythonic
"""
import os
import sys
import serial
import struct
sys.path.insert(0, os.path.abspath('include'))
from controllers import *
from messages import *


class Thorapt():

    # errors
    class Error(Exception): # general error; to be replaced with more specific ones
        pass

    class InvalidCommandError(Exception):
        pass

    def __init__(self, *port):

        # serial port configuration
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 0.1 # arbitrary
        self.ser.rtscts = True
        self.ser.rts = True
        self.channel = b'\x50' # channel for generic USB hardware unit

        self.override = False # incompatible commands are executed if value is set to 'True'

        if len(port)>0: # if no arguments provided, use default pySerial port
            self.ser.port = port[0] # take the port to be the first argument given
            self.open() # open port

    def open(self):
        """
        opens serial port and searches for occupied channels
        configures port to controller or that in the first occupied bay for multi-channel controllers
        """

        self.ser.open() # open port
        self.ser.write(b'\x05\x00\x00\x00%b\x01' % self.channel) # send request for hardware info to generic USB hardware unit
        data = self.ser.readline() # receive response
        if len(data) == 90 and data[:4] == b'\x06\x00\x54\x00': # check for correct type of response
            self.type_ = data[18:20] # read type of controller
            self.channel = data[5] # update to specific channel
            if self.type_ == '\x44': # check for brushless DC controller
                self.channels = [self.channel] # update to specific channel
                self.model_no = str(struct.unpack('<8s', data[10:18])[0], 'utf-8') # read model number
            elif self.type_ == '\x45': # check for multi-channel controller motherboard
                self.channels = [b'\x21', b'\x22', b'\x23', b'\x24', b'\x25', b'\x26', b'\x27', b'\x28', b'\x29', b'\x2A'] # add channels to all bays
                bays = [b'\x00', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\x09'] # bay values for checking
                for i, bay in enumerate(bays):
                    self.ser.write(b'\x60\x00%b\x00%b\x01' % (bay, self.channel)) # send request to determine bay occupancy to motherboard
                    data = self.ser.readline() # receive response
                    if len(data) == 6 and data[:3] == b'\x61\x00%b' % bay: # check for correct type of response
                        if data[3] == b'\x01':
                            pass # do not remove channel to occupied bay
                        elif data[3] == b'\x02':
                            del self.channels[i] # remove channel to unoccupied bay
                        else:
                            raise self.Error
                        self.channels.insert(0, b'\x11') # add channel to motherboard
                        self.channel = self.channels[1] # set channel to first occupied bay
                        """
                        self.channels is a list of active channels
                        self.channels[0] is the channel to the motherboard
                        access each bay by using self.channels[x] where x is its index among the occupied bays, starting from 1
                        eg. if bays 2, 4, 5 are used
                        access bay 2 using self.channels[1]
                        access bay 4 using self.channels[2]
                        access bay 5 using self.channels[3]
                        """
                    else:
                        raise self.Error
            else:
                raise self.Error
        else:
            raise self.Error

    def close(self):
        self.ser.close()

    # to accomodate use of with statement
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # class methods
    def check(message):
        if message in messages:
            controller = self.model_no
            if controller not in controllers:
                controller = controller[:-1] + 'x'
        else:
            raise self.InvalidCommandError("command does not exist")
        c = controller not in controllers
        m = message not in controllers[controller]
        if c:
            print("controller %s not supported" % self.model_no)
        elif self.override:
            print("command %s (%s) not supported by controller %s"
            % (messages[message], message, self.model_no))
        if self.override:
            print ("command executed at your own risk")
        else:
            raise self.InvalidCommandError("operation aborted; set override value to \'True\' to ignore error")

    def active_channels(self):
        return self.channels

    def set_channel(self, channel):
        if len(self.channels) > 1:
            # change channel
            self.channel = self.channels[channel]
        else:
            raise self.Error
        # update model number
        self.ser.write(b'\x05\x00\x00\x00%b\x01' % self.channel)
        data = self.ser.readline()
        if len(data) == 90 and data[:4] == b'\x06\x00\x54\x00':
            self.model_no = data[10:18]
        else:
            raise self.Error

    def get_channel(self):
        return self.channel

    # generic system control messages
    def mod_identify(self):
        check('0x0223')
        self.ser.write(b'\x23\x02\x00\x00%b\x01' % self.channel)

    def hw_get_info(self):
        self.ser.write(b'\x05\x00\x00\x00%b\x01' % self.channel)
        data = self.ser.readline()
        if len(data) == 90 and data[:4] == b'\x06\x00\x54\x00':
            self.serial_no = struct.unpack('<i', data[6:10])[0]
            self.model_no = str(struct.unpack('<8s', data[10:18])[0], 'utf-8')
            self.type_ = struct.unpack('<H', data[18:20])[0]
            self.firmware_ver = struct.unpack('<i', data[20:24])[0]
            self.hw_ver = struct.unpack('<H', data[84:86])[0]
            self.mod_state = struct.unpack('<H', data[86:88])[0]
            self.nch = struct.unpack('<H', data[88:90])[0]
            if self.type_ == 44:
                self.type_ = "multi-channel controller board"
            elif self.type_ == 45:
                self.type_ = "brushless DC controller"
