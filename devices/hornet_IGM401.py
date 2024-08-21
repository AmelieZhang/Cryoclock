# Code to communicate with a Hornet Vacuum gauge, model IGM401.
# Connection is via a usb-to-RS485 adapter.
#
# The serial communication specification is on page 32 of the Hornet manual.
#
# The software version '1769-107' is specific to the yellow Hornet. This will
#  likely be different for more recent devices.
#
# Note that to connect the Hornet to the rs485-to-usb adapter, I had to connect
#  it such that the "A" went to "B" connections. Apparently there are different
#  conventions when it comes to labelling the lines with "A" and "B". The
#  config that worked connected the (-) and (+) terminals together. Both data
#  lines are differential, so there is no harm in swapping them if you find that
#  the rs485-to-usb device you are using doesn't seem to work.


import numpy as np
import time
import serial

class Hornet_IGM401():

    def __init__(self, serial_addr, rs485_addr = "01"):

        self.device_timeout = 1.0# serial timeout
        self.query_delay = 0.1# for testing

        #Expected response length for error checking
        self.response_length = 12# Manual says all responses are 13 characters long including the <CR>

        # open the connection
        self.addr = serial_addr
        self.rs485_addr = rs485_addr# rs485 hexadecimal address in string form
        self.open_connection()
        time.sleep(0.05)# arbitrarily wait, for safety

        # test the connection
        # prints only the version of the controller if successful
        s = self.test_connection()

    # connect to the device
    def open_connection(self):
        """
        Make the connection to the device.
        Redefine for subclasses.
        """
        # The default communication settings are:
        # 19,200 baud rate, 8 data bits, No Parity, 1 stop bit [Factory default; 19,200, 8, N, 1].
        # From page 32 of the manual.

        print(f"Opening connection to {self.addr}")
        # Some of these I put in are defaults already, but I am being explicit.
        self.baudrate = 19200
        self.device = serial.Serial(self.addr,
                                    baudrate=self.baudrate,
                                    bytesize = serial.EIGHTBITS,
                                    parity = serial.PARITY_NONE,
                                    stopbits = serial.STOPBITS_ONE,
                                    timeout=self.device_timeout,
                                    xonxoff = False,
                                    rtscts = False,
                                    dsrdtr = False,
                                    )

    def close_connection(self):
        """
        Close the connection to the device.
        """
        self.device.close()

    def test_connection(self):
        s = self.get_version()
        #print(type(s))
        print(s)

        # The serial number for the Hornet is on the bottom of the unit
        # (I'm taking the one on the siler bottom and not on the yellow back).
        # The old Hornet that makes a high pitched noise:
        #   SN: 14I218T is '1769-107'
        # The new Hornet (Nov 2023)
        #   SN: 23K00505 is '3351-101'
        #
        if '3351-101' not in s:# This check is specific to each Hornet
            print("Testing connection failed. Wrong device or connection failed.")
        return s

    # basic routines for writing commands and reading responses

    def write(self, command):
        """
        Write a command to the device and parse the response.
        """
        #self.device.reset_input_buffer()
        #self.device.reset_output_buffer()
        #print("start write fn")
        command = f"{command}\r".encode('ascii')# '\r' is <CR>
        #print(f"command: |{command}|")
        self.device.write(command)
        self.device.flush()

        # Read response and sanitize it a little
        response = self.device.read_until('\r'.encode('ascii'))
        #print(f"response: |{response}|")
        response = response.decode('ascii').strip()
        #print(f"response: |{response}|")

        return response

    def query(self, command):
        """
        Query the device once return the response (as a string).
        """
        # command is only the characters after the '#xx' (and no ending <CR>)

        s = self.write(f"#{self.rs485_addr}{command}")# tell device to transmit something next

        # Check for errors
        if len(s) != self.response_length:# all responses should be a consistent length
            print(f"Incorrect response length: |{s}|")
        elif s[0] == '?':
            print(f"Error message: |{s}|")

        elif s[0] != '*':
            print(f"Unknown first character of response: |{s}|")

        elif s[1:3] != self.rs485_addr:
            print(f"Incorrect rs485 address: |{s}|")

        return s

    # convenience functions

    def get_version(self):
        """Get the Hornet's software version."""
        s = self.query("VER")
        s = s[4:]#extract the software version
        return s

    def get_ig_status(self):
        s = self.query("IGS")
        is_on = bool(s[4])
        return is_on

    def get_ig_pressure(self):
        # Assumes the pressure unit is in torr
        s = self.query("RD")
        f = float(s[4:])
        return f








if __name__ == '__main__':
    import matplotlib.pyplot as plt
    #import matplotlib.dates as mdate
    from datetime import datetime

    hornet = Hornet_IGM401(serial_addr = "COM7", rs485_addr = "01")

    # A simple test to measure the pressure over time
    def measure_pressure(wait_time = 10.0):
        while True:
            t = time.time()
            p = hornet.get_ig_pressure()
            wl = f"{t}, {p}"
            print(wl)
            time.sleep(wait_time)

    # A simple way to log the pressure from the Hornet over time.
    # This sort of functionality should really go in another class/file.
    # Use as: simple_p_log(filepath, 10.0)
    path = "C:/Users/Amar Vutha/Documents/vutha_lab/"
    path = "C:/Users/Amar Vutha/Documents/vutha_lab/cryoclock/pumping_manifold/hornet_pressure_logs/"
    filepath = path + "0000-00-00_hornet_p_log.txt"
    def simple_p_log(fn, wt = 10.0):
        with open(fn, 'a') as fp:
            while True:
                t = time.time()
                p = hornet.get_ig_pressure()
                wl = f"{t}, {p}"
                print(wl)
                fp.write(wl+'\n')
                fp.flush()
                time.sleep(wt)

    # All that follows should go in another class, but for now I will write it here.

    def read_simple_p_log(fn):
        data = np.genfromtxt(fn, delimiter=',')
        return data

    def plot_p_log(data):
        # Prune data where the IG is off
        ii = np.less(data[:,1], 1e9)
        data = data[ii]
        tt = np.array([datetime.fromtimestamp(x) for x in data[:,0]])
        yy = data[:,1]
        # Do the plotting
        f1 = plt.figure(70)
        f1.clf()
        ax1 = f1.add_subplot(111)
        ax1.plot(tt, yy, '.')
        #ax1.plot(datetime.fromtimestamp(data[:,0]), data[:,1])
        ax1.legend(['pressure'])
        #ax1.set_xlabel("Time (seconds since epoch)")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.grid()
        #ax1.set_yscale("log")
        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()





