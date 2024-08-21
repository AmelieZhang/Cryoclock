# -*- coding: utf-8 -*-
"""
A header for communicating with the NEXTorr D100-5 ion pump and neg pump
through the NIOPS-03 Power Supply controller.

2023-03-28 Scott Smale:
    I just want to connect, check connnection, and read the status of the
    ion pump and its current. Control can come later.
"""
# Todo:
# Some commands need a write and some need a query. It would be good to ensure
# that the user doesn't have to be careful about this.

# Fix "TM" command. It has multiple lines and so half of it is left behind.

# Commands can be terminated by either <CR> or <CR><LF> so says the manual.
# These are '\r' or '\r\n'.
# Choosing '\r\n' causes the controller to not respond after random number
# of requests. Using '\r' does not cause this error.





# Some notes I took while diagnosing the random communication failure issue.
# Some settings that I've tried:
# 5 sec between queries, 1 sec serial timeout, 0.1 sec between ask and enq
#   Failed after 34 times.
# 30 sec between queries, 1 sec serial timeout, 0.01 sec between ask and enq
#   Failed after 3 times.
# 10 sec between queries, 10 sec serial timeout, 5 sec between ask and enq
#   Failed after 6 times.
# 5 sec between queries, 1 sec serial timeout, 0.1 sec between ask and enq
#   Failed after 32 times. This is oddly similar to before.
#   Failed after 6 times. Okay, nearly the same number was just a fluke.
# 10 sec between queries, 1 sec serial timeout, 0.1 sec between ask and enq
#   Failed after 1 time. :(
#   Failed after 9 times. Adding self.device.flush() after resp. doesn't help.
# 10 sec between queries, 1 sec serial timeout, 0.1 sec between ask and enq
#   Trying just sending '\r' for command and response <ENQ>.
#   IT WORKED FOR 50 consequtive times!!
# 10 sec between queries, 1 sec serial timeout, 0.1 sec between ask and enq
#   Worked again 50 times! Even while eating the '\n'.
# 0.01 sec between queries, 0.5 sec serial timeout, 0.005 sec btwn ask and enq
#   These are the fastest timings I have checked as working (>100 times).
#   I am pretty sure this timing is now limited by the print commands.
#   I can't make it fail now. Success!




import time
import serial

class Nextorr_D100_5_pump():

    def __init__(self, address):

        self.enq = chr(5)#<ENQ>
        self.ack = chr(6)#<ACK>
        self.nak = chr(21)#<NAK>

        self.device_timeout = 0.5# serial timeout
        self.enq_delay = 0.01# delay between command and <ENQ>
        self.query_delay = 0.1# for testing
        
        # open the connection
        self.addr = address
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
        # The default communication baud rate is 115200 Bd, 8 data bits,
        # 1 stop-bit, without parity bit, flow control none.

        print(f"Opening connection to {self.addr}")
        # Some of these I put in are defaults already, but I am being explicit.
        self.baudrate = 115200
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
        if 'NIOPS.3 Feb 24 2014' not in s:
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
        command = f"{command}\r".encode('ascii')
        self.device.write(command)
        self.device.flush()

        # Read response and sanitize it a little
        response = self.device.read_until('\r'.encode('ascii'))
        #print(f"response: |{response}|")
        response = response.decode('ascii').strip()
        #print(f"response: |{response}|")

        # Clean up the extra '\n'.
        # This will timeout on responses that don't have it. But that is ok.
        n = self.device.read(1)
        #print(f"n: |{n}|")# debugging
        
        return response
        
    def query(self, command):
        """
        Query the device once return the response (as a string).
        """

        # Nearly all commands should respond with an <ACK> or <NAK>
        # Exceptions include the version command and the status command.
        # This function swallows the <ACK> and prints a notification when
        # there is a problem indictated by <NAK>.
        # Doing <ENQ> after a command that does not send <ACK> returns an
        # empty string because nothing has been transmitted.
        
        s = self.write(command)# tell device to transmit something next

        # Check for errors
        if len(s) == 1:
            if s == self.ack:#<ACK>
                #print("<ACK> (debug)")
                pass
            elif s == self.nak:#<NAK>
                print("<NAK> -> There is a Problem!")
            else:
                print("Unrecognized response code. Problem?!")

        # wait for it to prepare the response
        # needed for (at least) reading the ion pump current value
        # sleep(0.01) works about 93% of the time.
        # sleep(0.05) worked even less.
        # sleep(1.0) also failed after only a few.
        # Issue is likely the serial timeout, not this wait time.
        time.sleep(self.enq_delay)
        
        s = self.write(self.enq)# <ENQ>, tell the device to transmit it
        return s
            
    # convenience functions
    
    def get_version(self):
        """Get the controller's software version."""
        s = self.write("V")
        return s

    def get_status(self):
        s = self.write("TS")
        return s

    def get_ionpump_current(self):
        """
        Returns the ion pump current in nA.
        """
        s = self.query("I")
        #print(f"Raw query: {s}")
        
        # Transform this hex number into a 16 bit binary string
        bin_str = f"{int(s,16):0>16b}"
        #print(f"Binary string: {bin_str}")
        
        # Get the first two digits of the binary number
        rr = bin_str[0:2]
        #print(f"Two highest bits: {rr}")
        
        # Get the remaining binary number that contains the pressure
        vv = bin_str[2:]
        #print(f"Remaining bits: {vv}")
        
        # and convert it to an integer
        vv = int(vv, 2)
        #print(f"Integer value: {vv}")
        
        # Get the step (ie. prefactor) according to rr in units of nA
        # This could be more clever, but its good enough for now.
        if rr == "00":# 0-10 μA
            step = 1.0# 1 nA
        elif rr == "01":#10 μA - 1 mA
            step = 100.0# 0.1 uA or 100.0 nA
        elif rr == "10":#1 mA - 1OO mA
            step = 10000.0# 10 uA or 10000.0 nA
        else:# error so return garbage
            step = -9999999.0
            
        # Compute the float value by mulitplying by step
        p = step * vv
        return p

    def get_ionpump_voltage(self):
        """
        Returns ion pump voltage in kV.
        """
        s = self.query("U")
        # convert to a float in units of kV
        ii = int(s,16)
        voltage = 1e-3 * ii
        return voltage

    def set_ionpump_voltage(self, val):
        """
        Set the ion pump voltage.
        val must be a 4 digit integer from 1200 to 6000 V.
        """
        val = int(val)
        s = self.query(f"U{val}")
        return s

    def get_ionpump_pressure(self):
        # Note that this depends on how big the controller thinks the pump is.
        # I don't know if the defaults are correct. Take value with a grain
        # of salt.
        s = self.query("TT")
        # Specifying other of Tx here gives the value in different units.
        return s

    def get_ionpump_AtoPconst(self):
        # This is the conversion between current and Torr.
        # Example: "Pump Constant 65 A/Torr<CR>"
        s = self.query("TK")
        return s

    # Not implemented is turning the ion pump on or off remotely.
    # Send "B" to turn off.
    # Send "G" to turn on.

    def get_on_time(self):
        s = self.query("TM")
        return s

    # To control the neg pump:
    # Send "BN" to turn it off
    # Send "GN" to turn it on (Make sure you choose an activation method first!)
    # Change activation method
    #       Mx<CR>[ <LF>]
    #         x 1 Activation
    #           2 Timed Activation
    #           3 Conditioning
    #           4 Timed Conditioning

# Both of these commands worked after a refresh.
# >>> neg.write("M1")
# '$'
#
# >>> neg.write("M2")
# '$'


if __name__ == '__main__':
    
    neg = Nextorr_D100_5_pump(address = "COM5")

    # Test what the minimum time between queries can be and still be reliable.
    def test_repeat_query():
        for i in range(100):
            print(i)
            #neg.get_ionpump_voltage()
            val = neg.get_ionpump_current()
            print(val)
            time.sleep(neg.query_delay)

            #neg.get_ionpump_voltage()
            #time.sleep(neg.query_delay/2.0)
            #neg.get_ionpump_current()
            #time.sleep(neg.query_delay/2.0)
    
    # A simple way to log the ion pump current from the NexTorr over time.
    # This sort of functionality should really go in another class/file.
    # Use as: simple_p_log(filepath, 10.0)
    path = "C:/Users/Amar Vutha/Documents/vutha_lab/cryoclock/pumping_manifold/nextorr_current_logs/"
    filepath = path + "0000-00-00_nextorr_I_log.txt"
    def simple_I_log(fn, wt = 111.0):
        with open(fn, 'a') as fp:
            while True:
                t = time.time()
                V = neg.get_ionpump_voltage()
                I = neg.get_ionpump_current()
                wl = f"{t}, {V}, {I}"
                print(wl)
                fp.write(wl+'\n')
                fp.flush()
                time.sleep(wt)

