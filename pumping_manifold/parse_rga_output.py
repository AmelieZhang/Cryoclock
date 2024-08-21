# A class to read in the data files that are written out by the rga gui.

# Main goal is to take successive mass sweeps and plot them vs time.






# The structure of the data is as follows.
# MassSpecData-04439-20231214-200008.csv

# Data starts at 0.6 amu and ends at 110.5 amu (assuming the gui is doing a full scan).
# Data looks like this:
#2023/12/14 20:00:31.556,  110.400,  1.9712e-014,
#2023/12/14 20:00:31.576,  110.500,  3.0656e-014,
#2023/12/14 20:00:32.399,    0.600,  1.7672e-010,
#2023/12/14 20:00:32.419,    0.700,  1.6171e-010,
#2023/12/14 20:00:32.440,    0.800,  1.6117e-010,


# Choose a way to distinguish between emult on or off when plotting.



import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
import os


class RGA_file_parser():

    def __init__(self, device_serial):

        self.device_serial = device_serial

        self.data_state = {}
        self.data_default_state = { "DateTime":"2023-12-14 3:46:04 PM",
                                    "Caption":"CCU 4439 - Probe 224809",
                                    "Serial":"4439",
                                    "ScanSpeed":"48",
                                    "LowMass":"1",
                                    "HighMass":"110",
                                    "SamplesPerAMU":"10",
                                    "Mode":"Mass sweep",
                                    "Filament":"1",
                                    "EnableElectronMultiplier":"1",
                                    }


    def convert_config_datetime(self, s):
        # Convert the date time format that the file uses in the config section.
        # Note that this is the last saved time of the gui's config file, not this data file's time.
        # Var s is a string containing the date and time
        datetime_code = "%Y-%m-%d %I:%M:%S %p"
        d = datetime.strptime(s, datetime_code)
        #print(d)
        return d

    def convert_data_datetime(self, s):
        # Convert the date time format that the file uses in each data line.
        # Var s is a string containing the date and time
        datetime_code = "%Y/%m/%d %H:%M:%S.%f"
        d = datetime.strptime(s, datetime_code)
        #print(d)
        return d

    def convert_filename_datetime(self, s):
        # Convert the date time format in the file name of each file.
        # Var s is the filename as a string
        s = s[19:-4]# trim everything but the date
        datetime_code = "%Y%m%d-%H%M%S"
        d = datetime.strptime(s, datetime_code)
        #print(d)
        return d

    def convert_startend_datetime(self, s):
        # Convert datetime from "2023-12-24 15:23:55" to datetime
        datetime_code = "%Y-%m-%d %H:%M:%S"
        d = datetime.strptime(s, datetime_code)
        #print(d)
        return d

    def check_for_one_header(self, dir):
        # Run through all of the files in a directory and print how many headers there were.
        # Testing function
        filename_match = "MassSpecData" # "MassSpecData" #"MassSpecData-04439-20231219-070034.csv"
        rga_files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and filename_match in f]
        print(rga_files)
        for fn in rga_files:
            print(fn)
            with open(os.path.join(dir,fn), 'r') as fp:
                for line in fp.readlines():
                    if "<ConfigurationData>" in line:
                        print("ConfigurationData")


    def parse_mass_spec_data_line(self, line):
        ll = line.strip().split(',')
        t = self.convert_data_datetime(ll[0].strip())# date/time
        m = float(ll[1].strip())# mass in amu
        p = float(ll[2].strip())# partial pressure (torr unless someone changes the gui setting)
        return t,m,p

    def filter_mass(self, mass, check):
        # Return true if the data with this mass is to be kept
        if check == "All":
            return True
        elif check == "Int" and mass == int(mass):
            return True
        elif type(check) is list and mass in check:
            return True
        else:
            return False

    def comb_file(self, filename, options):
        """
        Read a file and combs through it for the data needed.

        options is a dict with named elements that specify which data to keep.
        options["Mode"] = ["Mode sweep"] or ["Trend"] or ["Mass sweep", "Trend"]
        options["AMU"] = "All" or "Int" or list of explicit masses to keep
        """

        data = []
        with open(filename, 'r') as fp:
            fcd = {}# file config dictionary
            parse_mode = 'c'# 'c' for config, 'm' for data mass spec

            lines = fp.readlines()# read the entire file

            ii = 0
            while ii < len(lines):
                line = lines[ii]
                #print(line.strip())

                if parse_mode == 'c':# reading config lines
                    ll = line.strip()

                    if "DateTime=" in ll:
                        fcd["ConfigFileDateTime"] = self.convert_config_datetime(ll[10:-1])
                        #print(fcd["ConfigFileDateTime"])
                    elif "Caption=" in ll:
                        fcd["Caption"] = ll[9:-1]
                        #print(fcd["Caption"])
                    elif "Serial=" in ll:
                        fcd["Serial"] = ll[8:-1]
                        #print(fcd["Serial"])
                    elif "ScanSpeed=" in ll:
                        fcd["ScanSpeed"] = float(ll[11:-1])
                        #print(fcd["ScanSpeed"])
                    elif "LowMass=" in ll:
                        fcd["LowMass"] = int(ll[9:-1])
                        #print(fcd["LowMass"])
                    elif "HighMass=" in ll:
                        fcd["HighMass"] = int(ll[10:-1])
                        #print(fcd["HighMass"])
                    elif "SamplesPerAMU=" in ll:
                        fcd["SamplesPerAMU"] = int(ll[15:-1])
                        #print(fcd["SamplesPerAMU"])
                    elif "Mode=" in ll and ll[0] == 'M':
                        val = ll[6:-1]
                        if val in ["Mass sweep", "Trend"]:
                            fcd["Mode"] = val
                            #print(f"ii: {ii}")
                            #print(f'Mode: {fcd["Mode"]}')
                    elif "Filament=" in ll:
                        fcd["Filament"] = int(ll[10])# 0 or 1
                        #print(fcd["Filament"])
                    elif "EnableElectronMultiplier=" in ll:
                        fcd["EnableElectronMultiplier"] = int(ll[26])# 0 or 1
                        #print(fcd["EnableElectronMultiplier"])

                    elif "</ConfigurationData>" in ll:
                        parse_mode = 'm'
                        print("Config section ended.")

                    ii = ii + 1

                elif parse_mode == 'm':# reading data

                    try:

                        vals = self.parse_mass_spec_data_line(line)

                        #print(f"prior   : {vals}")

                        # filter data
                        filter = fcd["Filament"] == 1 and\
                                 fcd["Mode"] in options["Mode"] and\
                                 self.filter_mass(vals[1],options["AMU"])

                        if filter:
                            #print(f"filtered: {vals}")
                            data.append(vals)

                    except ValueError as e:
                        #print(e)
                        print("Continuing with next block...")
                        parse_mode = 'c'
                        # we failed to convert, so assume it is the start of the config file since it can't be the end of file.

                    ii = ii + 1

        return data, fcd

    def comb_filelist(self, dir, filelist, options):
        data_list = []
        for fn in filelist:
            data, fcd = self.comb_file(os.path.join(dir,fn), options)
            print(f"len(data): {len(data)}")
            if len(data) > 0:
                data_list.append(data)

        return np.vstack(data_list)

    def plot_p_vs_time(self, data):
        # Plot the pressure values vs time, regardless of mass.
        # Useful for getting the time of a mass sweep.

        tt = data[:,0]
        mm = data[:,1]
        pp = data[:,2]

        # Do the plotting
        f1 = plt.figure(90, figsize=[10,5])
        f1.clf()
        ax1 = f1.add_subplot(111)
        ax1.plot(tt, pp, '.', label = 'pressure')
        #ax1.legend()
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.grid(which='both')

        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()

    def plot_p_vs_time_for_single_m(self, data, mass_to_plot):
        # Plot a single mass.

        ii = np.equal(data[:,1], mass_to_plot)# pick out the single mass to plot
        tt = data[ii,0]
        mm = data[ii,1]
        pp = data[ii,2]

        # Do the plotting
        f1 = plt.figure(91, figsize=[10,5])
        f1.clf()
        ax1 = f1.add_subplot(111)
        ax1.plot(tt, pp, '.', label = 'pressure')
        #ax1.legend()
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.grid(which='both')

        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()


    def plot_p_vs_time_for_m(self, data, masses_to_plot, time_window = None):
        # Sort the data into each mass and plot.

        if masses_to_plot == "Int":# If want plot all integers, create list
            masses_to_plot = np.linspace(1, 110, 110)
            print(masses_to_plot)
        elif masses_to_plot == "All":# Not recommended
            masses_to_plot = np.linspace(0.6, 110.5, int(np.round((110.5-0.6)/0.1))+1)
        else:
            pass# assume masses_to_plot is a list


        f1 = plt.figure(91, figsize=[10,5])
        f1.clf()
        ax1 = f1.add_subplot(111)

        for mass in masses_to_plot:

            ii = np.equal(data[:,1], mass)# pick out the single mass to plot
            tt = data[ii,0]
            pp = data[ii,2]

            # Do the plotting for this mass
            ax1.plot(tt, pp, '.', label = f"{mass} Amu")

        ax1.legend()
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.set_xlim(time_window)
        ax1.grid(which='both')
        ax1.grid(which='major', color='tab:gray', linestyle='-')
        ax1.grid(which='minor', color='#CCCCCC', linestyle='--')

        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()

    def plot_one_mass_sweep(self, data, ref_time):

        index_in_sweep = np.argmin(np.abs(data[:,0]-ref_time))

        # Find the index of the start mass
        # Uses the fact that the mass diff between adjacent times of different sweeps should be negative.
        mass_diffs = np.diff(data[:,1])
        # When reference time is past the last data point or equal to it,
        # fudge the initial index to prevent out of bounds in mass_diffs.
        if index_in_sweep >= len(mass_diffs):
            index_in_sweep = index_in_sweep - 1

        i = index_in_sweep
        while mass_diffs[i] > 0:
            #print(f"{i} {mass_diffs[i]}")
            i = i - 1
            if i == -1:# prevent out of bounds errors
                break
        index_start = i + 1# Correct for offset

        i = index_in_sweep
        #while mass_diffs[i] > 0 and i < len(mass_diffs)-1:
        while mass_diffs[i] > 0:
            #print(f"{i} {mass_diffs[i]}")
            i = i + 1
            if i == len(mass_diffs):# prevent out of bounds errors
                break
        # No offset correction needed since indexing into mass not mass_diffs.
        index_end = i

        # Now grab the data needed
        mm = data[index_start:index_end+1,1]
        pp = data[index_start:index_end+1,2]

        # Do the plotting
        f1 = plt.figure(92, figsize=[10,5])
        f1.clf()
        ax1 = f1.add_subplot(111)
        #ax1.plot(mm, pp, '.', label = 'pressure')
        ax1.plot(mm, pp, '-', label = 'pressure')
        #ax1.legend()
        ax1.set_xlabel("Mass (amu)")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.margins(0.01, 0.05)
        ax1.set_ylim(bottom = 1e-14)
        ax1.set_xlim(left = 0.0)

        # Change major ticks to show every 10.
        ax1.xaxis.set_major_locator(mtk.MultipleLocator(10))
        # Change minor ticks to show every 2. (20/4 = 5)
        ax1.xaxis.set_minor_locator(mtk.AutoMinorLocator(5))
        # Turn grid on for both major and minor ticks and style minor slightly
        # differently.
        ax1.grid(which='major', color='tab:gray', linestyle='-')
        ax1.grid(which='minor', color='#CCCCCC', linestyle='--')

        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()

    def plot_mass_sweeps(self, data, ref_times, labels=None):

        f1 = plt.figure(93, figsize=[10,5])
        f1.clf()
        ax1 = f1.add_subplot(111)

        for ref_time in ref_times:
            index_in_sweep = np.argmin(np.abs(data[:,0]-ref_time))

            # Find the index of the start mass
            # Uses the fact that the mass diff between adjacent times of different sweeps should be negative.
            mass_diffs = np.diff(data[:,1])
            # When reference time is past the last data point or equal to it,
            # fudge the initial index to prevent out of bounds in mass_diffs.
            if index_in_sweep >= len(mass_diffs):
                index_in_sweep = index_in_sweep - 1

            i = index_in_sweep
            while mass_diffs[i] > 0:
                #print(f"{i} {mass_diffs[i]}")
                i = i - 1
                if i == -1:# prevent out of bounds errors
                    break
            index_start = i + 1# Correct for offset

            i = index_in_sweep
            #while mass_diffs[i] > 0 and i < len(mass_diffs)-1:
            while mass_diffs[i] > 0:
                #print(f"{i} {mass_diffs[i]}")
                i = i + 1
                if i == len(mass_diffs):# prevent out of bounds errors
                    break
            # No offset correction needed since indexing into mass not mass_diffs.
            index_end = i

            # Now grab the data needed
            mm = data[index_start:index_end+1,1]
            pp = data[index_start:index_end+1,2]

            # Do the plotting
            ax1.plot(mm, pp, '-', alpha=0.65, label = f"{data[index_in_sweep,0]}")


        ax1.set_xlabel("Mass (amu)")
        ax1.set_ylabel("Pressure (torr)")
        ax1.set_yscale("log")
        ax1.margins(0.01, 0.05)
        ax1.set_ylim(bottom = 1e-14)
        ax1.set_xlim(left = 0.0)
        if labels:
            ax1.legend(labels)
        else:
            ax1.legend()

        # Change major ticks to show every 10.
        ax1.xaxis.set_major_locator(mtk.MultipleLocator(10))
        # Change minor ticks to show every 2. (20/4 = 5)
        ax1.xaxis.set_minor_locator(mtk.AutoMinorLocator(5))
        # Turn grid on for both major and minor ticks and style minor slightly
        # differently.
        ax1.grid(which='major', color='tab:gray', linestyle='-')
        ax1.grid(which='minor', color='#CCCCCC', linestyle='--')

        f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
        f1.show()


    def get_filelist_for_times(self, dir, start_datetime, end_datetime):
        # Get a list of files in dir that could have data between start and end times.
        # Start and end are datetime objects

        data_file_interval = timedelta(hours=1.5)# time between data files (and pad it a little just in case)

        print(f"Searching for files between: {start_datetime} and {end_datetime}")

        filename_match = "MassSpecData"
        rga_files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and filename_match in f]
        #print(rga_files)

        filelist = []
        for fn in rga_files:
            #print(fn)
            # Get "time" of the file, should be the "start" time of the data.
            # The first data point in the file might be ahead or behind this time by a couple of seconds.
            ft = self.convert_filename_datetime(fn)
            if ft >= start_datetime-data_file_interval and ft <= end_datetime:
                #print(f"In domain: {ft}")
                filelist.append(fn)
                pass
            else:
                #print(f"Not in domain: {ft}")
                pass

        print("Done")
        return filelist



if __name__ == "__main__":

    d = "C:\\Users\\Amar Vutha\\Documents\\vutha_lab\\cryoclock\\pumping_manifold\\extorr_rga_data\\bucket\\"
    testfile = d+"MassSpecData-04439-20231221-221705.csv"

    mass_list = [2, 4, 6, 8, 12, 16, 18, 28, 32, 40, 44]# some interesting masses to plot by default


    rga_parser = RGA_file_parser("4439")
    #rga_parser.check_for_one_header(d)


    # Outgassing measurement after bake
    # Jan 9 at 1154am I restarted the trend trace
    # Jan 9 at 1204pm I closed the valve to the IVC
    # 104pm I opened the valve to the IVC
    #
    # mass_list = [2, 4, 18, 28, 32, 44]# some interesting masses
    # start_time = rga_parser.convert_startend_datetime("2024-01-09 11:00:00")
    # end_time = rga_parser.convert_startend_datetime("2024-01-09 23:00:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Trend"], "AMU":"Int"} )
    # rga_parser.plot_p_vs_time(data)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list)

    # Fast H2 outgassing measurement (that didn't actually catch the spike)
    #filelist = ["MassSpecData-04439-20240110-133147.csv", "MassSpecData-04439-20240110-140707.csv"]


    # Turbo valve closure (turbo failing)
    # Closed valve to turbo on Jan 24 at 652pm
    # Turned off rga filament Jan 26 at 451pm
    #
    # mass_list = [2, 4, 6, 8, 12, 16, 18, 28, 32, 40, 44]# some interesting masses
    # start_time = rga_parser.convert_startend_datetime("2024-01-23 00:00:00")
    # end_time = rga_parser.convert_startend_datetime("2024-01-26 17:00:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep"], "AMU":"Int"} )
    # rga_parser.plot_p_vs_time(data)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list)


    # Testing rga filament off and on check
    # Turned off rga filament Jan 26 at 451pm. Stopped gui sweeping 453pm.
    # Turned on rga filament again Jan 31 at 542pm.
    # Turned off rga filament at about 721pm.
    #
    # mass_list = [2, 4, 6, 8, 12, 16, 18, 28, 32, 40, 44]# some interesting masses
    # start_time = rga_parser.convert_startend_datetime("2024-01-26 13:00:00")
    # end_time = rga_parser.convert_startend_datetime("2024-01-31 19:21:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep"], "AMU":"Int"} )
    # rga_parser.plot_p_vs_time(data)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list)


    # Plot mass spectra during filament turn on as an example
    # Turned off rga filament Jan 26 at 451pm. Stopped gui sweeping 453pm.
    # Turned on rga filament again Jan 31 at 542pm.
    # Turned off rga filament at about 721pm.
    #
    # start_time = rga_parser.convert_startend_datetime("2024-01-26 13:00:00")
    # end_time = rga_parser.convert_startend_datetime("2024-01-31 19:21:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # ref_times = [rga_parser.convert_startend_datetime("2024-01-31 17:45:00"),
    #              rga_parser.convert_startend_datetime("2024-01-31 18:00:00"),
    #              rga_parser.convert_startend_datetime("2024-01-31 19:25:00"),]
    # # ref_times = [rga_parser.convert_startend_datetime("2024-01-31 19:20:00"),
    # #              rga_parser.convert_startend_datetime("2024-01-31 18:15:00")]
    # #labels = ["test1", "test2", "test3"]
    # time_window = [rga_parser.convert_startend_datetime("2024-01-31 17:40:00"),
    #                rga_parser.convert_startend_datetime("2024-01-31 19:40:00")]
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep"], "AMU":"All"} )
    # rga_parser.plot_p_vs_time(data)
    # #rga_parser.plot_p_vs_time_for_m(data, mass_list)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list, time_window)
    # rga_parser.plot_one_mass_sweep(data, ref_time)
    # rga_parser.plot_mass_sweeps(data, ref_times)
    # #rga_parser.plot_mass_sweeps(data, ref_times, labels)



    # Feb 28 turn on filament for leak check. Look at the time series until the leak checking started.
    # Turned on rga filament Feb 28 at 525pm.
    #
    # start_time = rga_parser.convert_startend_datetime("2024-02-28 17:20:00")
    # end_time = rga_parser.convert_startend_datetime("2024-03-31 12:00:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # ref_times = [rga_parser.convert_startend_datetime("2024-03-01 22:30:00"),
    #              #rga_parser.convert_startend_datetime("2024-01-31 18:00:00"),
    #              #rga_parser.convert_startend_datetime("2024-01-31 19:25:00"),
    #              ]
    # #labels = ["test1", "test2", "test3"]
    # time_window = [rga_parser.convert_startend_datetime("2024-02-28 17:20:00"),
    #                rga_parser.convert_startend_datetime("2024-03-02 17:20:00")]
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep"], "AMU":"All"} )
    # rga_parser.plot_p_vs_time(data)
    # #rga_parser.plot_p_vs_time_for_m(data, mass_list)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list, time_window)
    # rga_parser.plot_mass_sweeps(data, ref_times)
    # #rga_parser.plot_mass_sweeps(data, ref_times, labels)


    # # Mar 2 leak check. Plot time trace with Helium leak check. And outgassing measurements.
    # # Leak checked between about 227 and 229pm.
    # # Closed valve at 248pm. 1 hour hold time. Valve opened 348pm.
    # # Closed valve 442pm. Flowed Helium for 10 min hold time. Valve opened 452pm.
    # # Closed valve 505pm. 30 min hold time. Valve opened 535pm.
    # #
    # mass_list = [2, 4, 18, 28, 32, 44]
    # start_time = rga_parser.convert_startend_datetime("2024-03-02 14:00:00")
    # end_time = rga_parser.convert_startend_datetime("2024-03-02 23:00:00")
    # filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    # ref_times = [rga_parser.convert_startend_datetime("2024-03-02 14:00:00"),
    #              # rga_parser.convert_startend_datetime("2024-01-31 18:00:00"),
    #              # rga_parser.convert_startend_datetime("2024-01-31 19:25:00"),
    #              ]
    # #labels = ["test1", "test2", "test3"]
    # time_window = [rga_parser.convert_startend_datetime("2024-03-02 14:20:00"),
    #                rga_parser.convert_startend_datetime("2024-03-02 18:30:00")]
    # data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep", "Trend"], "AMU":"All"} )
    # rga_parser.plot_p_vs_time(data)
    # #rga_parser.plot_p_vs_time_for_m(data, mass_list)
    # rga_parser.plot_p_vs_time_for_m(data, mass_list, time_window)
    # rga_parser.plot_mass_sweeps(data, ref_times)
    # #rga_parser.plot_mass_sweeps(data, ref_times, labels)


    # Jul 3 valve closed to turbo+roughing pump and connecting bellows
    # Closed valve at 503pm
    # Turned off turbo pump at 700pm
    #
    mass_list = [2, 4, 18, 28, 32, 44]
    start_time = rga_parser.convert_startend_datetime("2024-07-02 14:00:00")
    end_time = rga_parser.convert_startend_datetime("2024-07-03 12:30:00")
    filelist = rga_parser.get_filelist_for_times(d, start_time, end_time)
    ref_times = [rga_parser.convert_startend_datetime("2024-07-02 19:00:00"),
                 # rga_parser.convert_startend_datetime("2024-01-31 18:00:00"),
                 # rga_parser.convert_startend_datetime("2024-01-31 19:25:00"),
                 ]
    #labels = ["test1", "test2", "test3"]
    time_window = [rga_parser.convert_startend_datetime("2024-07-02 14:20:00"),
                   rga_parser.convert_startend_datetime("2024-07-03 12:30:00")]
    data = rga_parser.comb_filelist(d, filelist, {"Mode":["Mass sweep", "Trend"], "AMU":"All"} )
    rga_parser.plot_p_vs_time(data)
    #rga_parser.plot_p_vs_time_for_m(data, mass_list)
    rga_parser.plot_p_vs_time_for_m(data, mass_list, time_window)
    rga_parser.plot_mass_sweeps(data, ref_times)
    #rga_parser.plot_mass_sweeps(data, ref_times, labels)









#{"Mode":["Trend"], "AMU":"All"}
#{"Mode":["Mass sweep","Trend"], "AMU":"All"}
#{"Mode":["Mass sweep"], "AMU":"All"}






# Important parameters marked below.
# <ConfigurationData> ##### Line 1
#    <CommunicationParameters
#       Port="COM4"
#       Baud="9600"
#       PacketFrequency="5.0"
#       PacketTimeout="1.0"
#       CommunicationsType="1"
#       UserFrequency="5.0"
#       UserTimeout="1.0"
#       NamedPort=""
#    />
#
#    <ConfigurationParameters
#       Filename="C:\Users\Amar Vutha\Desktop\RGA CONFIG FILES\rga_working_cal.cfg"
#       Description="General RGA running file."
#       TimeStamp="07e7000c0004000e000f002e000402a1"
#       DateTime="2023-12-14 3:46:04 PM" ################# (for uniqueness)
#       Caption="CCU 4439 - Probe 224809" ################# (check correct device)
#       Serial="4439" ################# (check correct device)
#       Model="100"
#       VacuumPlusVersion="1.0.47"
#    />
#
#    <ScanParameters
#       ScanSpeed="48" #################
#       LowMass="1" #################
#       HighMass="110" #################
#       SamplesPerAMU="10" #################
#    />
#
#    <OperatingParameters ################# all parameters here important for consistency between data sets
#       Mode="Mass sweep" #################
#       Focus1="-22"
#       Focus2="-68"
#       ElectronEnergy="70.0"
#       FilamentEmission="2.0"
#       AutoZero="Off"
#       ScanMode="Sweep"
#       Filament="1" ################# is filament on
#       PressureUnits="Torr"
#       EnableElectronMultiplier="1" #################
#       MultiplierVoltage="1035"
#       FilamentForceOffStartup="0"
#       TargetPressure="1.00e-007"
#       TargetPressureUnits="Torr"
#       MultiplierScale="1.00e+003"
#    />
#
#    <CalibrationParameters
#       LowCalMass="1"
#       LowCalResolution="640"
#       LowCalPosition="0.38"
#       LowCalIonEnergy="5.0"
#       HighCalMass="100"
#       HighCalResolution="1340"
#       HighCalPosition="0.40"
#       HighCalIonEnergy="5.0"
#       TotalAmpOffset="2000"
#       PartialAmpOffset="2085"
#       TotalIntegratingCap="10.00"
#       PartialIntegratingCap="3.00"
#       RFSettleTime="50"
#       SWSettleTime="10"
#       Pirani1ATM="1.93610"
#       PiraniZero="0.26000"
#       PiraniAutoRecalibrate="0"
#       PartialSensitivity="6.00e-004"
#       TotalSensitivity="1.00e+001"
#       debug="0"
#       DisablePressureProtection="1760869325799608300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000.000000"
#       FilamentControlP="-160000.000000"
#       FilamentControlI="10000.000000"
#       FilamentControlD="0.000000"
#       FilamentControlW="0.000000"
#       FilamentControlG="0.000000"
#       GroundThreshold="50.000000"
#       GroundThresholdVoltage="0.005000"
#       PiraniThresholdVoltage="0.450000"
#       ExternalIonSupply="0"
#    />
#
#    <LogFileParameters
#       Mode="2"
#       FileName=""
#       DirectoryName="C:\Users\Amar Vutha\Documents\vutha_lab\cryoclock\pumping_manifold\extorr_rga_data\bucket"
#       CreationOption="1"
#       NSweeps="15"
#       FileRecordingOn="1"
#    />
#
#    <MassTableParameters
#       Samples="1500"
#       AudioOutput="1"
#    >
#        <Mass1
#             Enabled="1"
#             Sound="0"
#             Mass="1"
#             Description=""
#             Color="Purple"
#             Dwell="21 ms"
#             HighWarning="0"
#             HighAlarm="0"
#             LowWarning="0"
#             LowAlarm="0"
#        />
#        ...
#        <Mass12
#             Enabled="1"
#             Sound="0"
#             Mass="78"
#             Description=""
#             Color="Gray"
#             Dwell="21 ms"
#             HighWarning="0"
#             HighAlarm="0"
#             LowWarning="0"
#             LowAlarm="0"
#        />
#    </MassTableParameters>
#
#    <PrintingParameters
#       InvertColors="1"
#       ShowConfigurationFile="1"
#       ShowDescription="1"
#       ShowTotalPressure="1"
#       ShowPiraniPressure="1"
#       DateFormat=""
#       TimeFormat=""
#    />
#
#    <GraphParametersData>
#       <GraphParameters
#              HScale="1"
#       >
#           <Y-Axis
#                ScaleAbsolute="329"
#                ZeroAbsolute="78"
#                Mode="1"
#           />
#       </GraphParameters>
#       <GraphParameters
#              HScale="1"
#       >
#           <Y-Axis
#                ScaleAbsolute="350"
#                ZeroAbsolute="97"
#                Mode="0"
#           />
#       </GraphParameters>
#    </GraphParametersData>
#
#    <WindowParameters>
#        <Frame
#             flags="2"
#             showCmd="3"
#             ptMinPosition.x="-1"
#             ptMinPosition.y="-1"
#             ptMaxPosition.x="-8"
#             ptMaxPosition.y="-31"
#             rcNormalPosition.left="26"
#             rcNormalPosition.top="68"
#             rcNormalPosition.right="910"
#             rcNormalPosition.bottom="417"
#        />
#        <Setup
#             flags="0"
#             showCmd="1"
#             ptMinPosition.x="-1"
#             ptMinPosition.y="-1"
#             ptMaxPosition.x="-1"
#             ptMaxPosition.y="-1"
#             rcNormalPosition.left="1436"
#             rcNormalPosition.top="46"
#             rcNormalPosition.right="1916"
#             rcNormalPosition.bottom="922"
#        />
#        <Main
#             flags="2"
#             showCmd="3"
#             ptMinPosition.x="-32000"
#             ptMinPosition.y="-32000"
#             ptMaxPosition.x="-1"
#             ptMaxPosition.y="-1"
#             rcNormalPosition.left="52"
#             rcNormalPosition.top="52"
#             rcNormalPosition.right="1492"
#             rcNormalPosition.bottom="811"
#        />
#    </WindowParameters>
#
#    <PlotParameters
#       BkColor="Pale green"
#       LineColor="Maroon"
#       ScanColor="Olive"
#       MouseWheel="0"
#       LogYAxis="1"
#       PressureLogYAxis="1"
#       PiraniColor="Red"
#       TotalColor="Blue"
#    />
#
#    <Outputs
#       DegasCurrent="2.3892"
#       ElectronicsTemperature="39.3492"
#       PowerSupply="23.9327"
#       FilamentVoltage="1.4242"
#       FilamentResistance="0.4592"
#       SensorTemperature="36.5091"
#       Source1Current="1.1606"
#       Source2Current="0.8398"
#       RFAmpVoltage="7.6638"
#       PiraniCorr="-0.1204"
#       PiraniTemp="-0.1198"
#       PiraniPress="-0.2687"
#       GroundReference="-0.0033"
#       DCPlusFB="2.4065"
#       DCMinusFB="2.4069"
#       FilamentDACFine="2047.0000"
#       FilamentDACCoarse="2895.0000"
#       ReferenceVoltage="2.4964"
#       Focus1="-21.9739"
#       Focus2="-67.9638"
#       FilamentPWM="63.7150"
#       FilamentStatus="3"
#       BACurrent="-1.0780e-012"
#       DegasTimeLeft="0"
#       PiraniPressureOut="1.0000e-004"
#       TotalPressureOut="-1.0780e-010"
#    />
#
# </ConfigurationData>





# https://stackoverflow.com/questions/46366461/3d-waterfall-plot-with-colored-heights
# def waterfall_plot(fig,ax,X,Y,Z):
#     '''
#     Make a waterfall plot
#     Input:
#         fig,ax : matplotlib figure and axes to populate
#         Z : n,m numpy array. Must be a 2d array even if only one line should be plotted
#         X,Y : n,m array
#     '''
#     # Set normalization to the same values for all plots
#     norm = plt.Normalize(Z.min().min(), Z.max().max())
#     # Check sizes to loop always over the smallest dimension
#     n,m = Z.shape
#     if n>m:
#         X=X.T; Y=Y.T; Z=Z.T
#         m,n = n,m
#
#     for j in range(n):
#         # reshape the X,Z into pairs
#         points = np.array([X[j,:], Z[j,:]]).T.reshape(-1, 1, 2)
#         segments = np.concatenate([points[:-1], points[1:]], axis=1)
#         lc = LineCollection(segments, cmap='plasma', norm=norm)
#         # Set the values used for colormapping
#         lc.set_array((Z[j,1:]+Z[j,:-1])/2)
#         lc.set_linewidth(2) # set linewidth a little larger to see properly the colormap variation
#         line = ax.add_collection3d(lc,zs=(Y[j,1:]+Y[j,:-1])/2, zdir='y') # add line to axes
#
#     fig.colorbar(lc) # add colorbar, as the normalization is the same for all, it doesent matter which of the lc objects we use
#
# import numpy as np; import matplotlib.pyplot as plt
# from matplotlib.collections import LineCollection
# from mpl_toolkits.mplot3d import Axes3D
#
# # Generate data
# x = np.linspace(-2,2, 500)
# y = np.linspace(-2,2, 40)
# X,Y = np.meshgrid(x,y)
# Z = np.sin(X**2+Y**2)
# # Generate waterfall plot
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# waterfall_plot(fig,ax,X,Y,Z)
# ax.set_xlabel('X') ; ax.set_xlim3d(-2,2)
# ax.set_ylabel('Y') ; ax.set_ylim3d(-2,2)
# ax.set_zlabel('Z') ; ax.set_zlim3d(-1,1)




#The test files and how many xml config data files there are in each one
# MassSpecData-04439-20231212-200015.csv
# ConfigurationData
# MassSpecData-04439-20231214-001206.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231201-172315.csv
# ConfigurationData
# MassSpecData-04439-20231201-190009.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231202-170209.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231201-180003.csv
# ConfigurationData
# MassSpecData-04439-20231213-200014.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231214-024821.csv
# ConfigurationData
# MassSpecData-04439-20231130-210202.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231130-170014.csv
# ConfigurationData
# MassSpecData-04439-20231213-000019.csv
# ConfigurationData
# MassSpecData-04439-20231213-190002.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231214-030012.csv
# ConfigurationData
# MassSpecData-04439-20231213-220747.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231219-030043.csv
# ConfigurationData
# MassSpecData-04439-20231218-220151.csv
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231218-090128.csv
# ConfigurationData
# MassSpecData-04439-20231213-120008.csv
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# ConfigurationData
# MassSpecData-04439-20231215-040012.csv
# ConfigurationData
# MassSpecData-04439-20231215-030009.csv