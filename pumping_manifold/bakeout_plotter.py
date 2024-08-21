# Open and parse data files created by various devices used during a bakeout.
#
# Devices:
# Hornet P gauge
# Thorlabs TSP01 temperature sensor


import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt


def read_simple_hornet_p_log(fn):
    data = np.genfromtxt(fn, delimiter=',')
    return data

def read_tsp_T_log(fn):
    # simple function
    # ignore header lines to start
    # File columns:
    # Time [s]	Date	Time	Temperature[°C]	Humidity[%]	TH1[°C]	TH2[°C]

    #data = np.genfromtxt(fn, delimiter='\t', skip_header=6, dtype=(np.int32, ))# does not parse the date

    data = []
    with open(fn, 'r') as fp:
        for header_ii in range(0,6):# move over the header lines
            fp.readline()
        for line in fp:
            ln = line.split('\t')
            #print(ln)
            dd = ln[1] + " " + ln[2]# create a single string for the datetime
            dd = datetime.strptime(dd, "%b %d %Y %H:%M:%S")# convert to datetime
            #print(dd)
            # Convert each element to float, super simple for now
            ln[0] = np.float64(ln[0])
            ln[1] = dd
            ln.pop(2)
            ln[2] = np.float64(ln[2])
            ln[3] = np.float64(ln[3])
            ln[4] = np.float64(ln[4])
            ln[5] = np.float64(ln[5])
            #print(ln)
            data.append(ln)
    return np.array(data)#.transpose()

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
    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()

def plot_T_log(data):
    #tt = data[0,:]# simple incremental time
    tt = data[1,:]# datetime time
    TH0 = data[2,:]
    TH1 = data[4,:]
    TH2 = data[5,:]
    f1 = plt.figure(71)
    f1.clf()
    ax1 = f1.add_subplot(111)
    ax1.plot(tt, TH0, '.', label="TH0")
    ax1.plot(tt, TH1, '.', label="TH1")
    ax1.plot(tt, TH2, '.', label="TH2")
    ax1.legend()
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Temperature (C)")
    ax1.set_yscale("linear")
    ax1.grid()
    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()

# Not the most useful function since the time steps are so small so it is noisy.
# Would need to average to get a meaningful plot.
def plot_dTdt(data):
    #tt = data[:,0]# simple incremental time
    tt_T = data_T[:,1]# datetime time
    TH0_T = data_T[:,2]
    TH1_T = data_T[:,4]
    TH2_T = data_T[:,5]

    dtt = np.diff(data[:,0])

    dTH0 = np.diff(TH0)# take the differences
    dTH0 = dTH0/dtt*60# convert to C/minute
    dTH1 = np.diff(TH1)
    dTH1 = dTH1/dtt*60
    dTH2 = np.diff(TH2)
    dTH2 = dTH2/dtt*60

    tt = tt[1:]# plot according to the end of the interval

    f1 = plt.figure(72)
    f1.clf()
    ax1 = f1.add_subplot(111)
    ax1.plot(tt, dTH0, '.', label="TH0 dT/dt")
    ax1.plot(tt, dTH1, '.', label="TH1 dT/dt")
    ax1.plot(tt, dTH2, '.', label="TH2 dT/dt")
    ax1.legend()
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Temperature change (C/min)")
    ax1.grid()
    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()

def plot_p_and_T(data_p, data_T, actions = None):
    # Prune data where the IG is off
    ii = np.less(data_p[:,1], 1e9)
    data_p = data_p[ii]
    tt_p = np.array([datetime.fromtimestamp(x) for x in data_p[:,0]])
    yy_p = data_p[:,1]

    tt_T = data_T[:,1]# datetime time
    TH0_T = data_T[:,2]
    TH1_T = data_T[:,4]
    TH2_T = data_T[:,5]

    # Do the plotting
    f1 = plt.figure(75)
    f1.clf()
    ax1 = f1.add_subplot(211)
    ax1.plot(tt_p, yy_p, '.', ms=2.0, label = 'pressure')
    #ax1.legend()
    #ax1.set_xlabel("Time")
    ax1.set_ylabel("Pressure (torr)")
    ax1.set_yscale("log")
    ax1.grid(which='both')
    ax1.tick_params(axis='x', labelbottom=False)

    ax2 = f1.add_subplot(212, sharex=ax1)
    ax2.plot(tt_T, TH0_T, '.', ms=2.0, label="TH0: SS breadboard")
    ax2.plot(tt_T, TH1_T, '.', ms=2.0, label="TH1: top plate")
    ax2.plot(tt_T, TH2_T, '.', ms=2.0, label="TH2: bot plate")
    ax2.legend()
    ax2.set_ylim([15, 120])
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Temperature (C)")
    ax2.set_yscale("linear")
    #ax2.tick_params(axis='x', labelrotation=45, 'labelright')
    f1.autofmt_xdate()
    ax2.grid()

    if actions != None:
        # iterate over the actions and draw vertical grid lines on each plot
        for a in actions:
            dd = datetime.strptime(a[0], "%Y-%m-%d %I:%M%p")# convert to datetime
            ax1.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)
            ax2.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)

    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()


if __name__ == '__main__':

    path = "C:/Users/Amar Vutha/Documents/vutha_lab/cryoclock/pumping_manifold/"

    #hornet_p_log_fn = path+"hornet_pressure_logs/2023-12-03_hornet_p_log.txt"
    #hornet_p_log_fn = path+"hornet_pressure_logs/2023-12-01b_hornet_p_log.txt"

    #tsp_T_log_fn = path+"thorlabs_temperature_logs/2023-12-03_thorlabs_t_logs.txt"
    #tsp_T_log_fn = path+"thorlabs_temperature_logs/2023-12-10_thorlabs_t_logs.txt"

    #hornet_data = read_simple_hornet_p_log(hornet_p_log_fn)
    #tsp_data = read_tsp_T_log(tsp_T_log_fn)


    # hornet_p_log_fn_list = [path+"hornet_pressure_logs/2023-12-01b_hornet_p_log.txt",
    #                         #path+"hornet_pressure_logs/2023-12-02a_hornet_p_log.txt",
    #                         path+"hornet_pressure_logs/2023-12-02b_hornet_p_log.txt",
    #                         path+"hornet_pressure_logs/2023-12-03_hornet_p_log.txt",
    #                         ]
    tsp_T_log_fn_list = [path+"thorlabs_temperature_logs/2024-06-04_thorlabs_t_logs.txt",
                         ]

    # hornet_data_list = []
    # for hornet_fn in hornet_p_log_fn_list:
    #     #print(hornet_fn)
    #     data = read_simple_hornet_p_log(hornet_fn)
    #     #print(f"data.shape: {data.shape}")
    #     hornet_data_list.append(data)
    #     #print(hornet_data_list)
    # hornet_data = np.vstack(hornet_data_list)
    # #print(hornet_data.shape)

    tsp_data_list = []
    for tsp_fn in tsp_T_log_fn_list:
        #print(tsp_fn)
        data = read_tsp_T_log(tsp_fn)
        #print(f"data.shape: {data.shape}")
        tsp_data_list.append(data)
        #print(tsp_data_list)
    tsp_data = np.vstack(tsp_data_list)
    #print(tsp_data.shape)

    actions = [ ["2023-12-03 7:34PM", "Start of bake log spreadsheet."],

    ]

    #plot_p_log(hornet_data)
    plot_T_log(tsp_data)
    #plot_dTdt(tsp_data)

    #plot_p_and_T(hornet_data, tsp_data, actions)
    #plot_p_and_T(hornet_data, tsp_data)
