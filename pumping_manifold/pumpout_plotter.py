# Open and parse data files created by various devices used during pumping out of a vacuum chamber at low pressure.
#
# Devices:
# Hornet P gauge
# RGA
# NexTorr D100 ion pump/getter pump

# todo:
# grab rga from bucket folder and load it into memory (maybe a separate class/persistent thing)
# plot either a mass spec from a particular time or plot a selected set of amu values from a seqeuence of mass specs vs time
# grab ion pump current




import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt


def read_simple_hornet_p_log(fn):
    data = np.genfromtxt(fn, delimiter=',')
    return data

def read_simple_nextorr_I_log(fn):
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
    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()

def plot_i_log(data_I, time_focus = None, actions = None):

    # change data with 0 nA current to be 0.1 nA and keep and index of these points.
    zeros_ii = np.less(data_I[:,2], 0.001)# < 0.001 nA and it can only output 0, 1, 2, ... nA.
    data_I[zeros_ii,2] = 0.1

    tt_I = np.array([datetime.fromtimestamp(x) for x in data_I[:,0]])
    yy_V = data_I[:,1]

    tt_I_on = tt_I[~zeros_ii]
    yy_I_on = data_I[~zeros_ii,2]

    tt_I_off = tt_I[zeros_ii]
    yy_I_off = data_I[zeros_ii,2]


    # Do the plotting
    f1 = plt.figure(76)
    f1.clf()

    ax2 = f1.add_subplot(111)
    ax2.plot(tt_I_on, yy_I_on, '.', ms=2.0, color = "tab:blue", label = 'Ion pump I')
    ax2.plot(tt_I_off, yy_I_off, '.', ms=2.0, color = "tab:cyan", label = "Zero current")
    ax2.plot(tt_I, yy_V, '.', ms=2.0, color = "tab:orange", label = 'Ion pump V', zorder = -1)
    ax2.legend()
    #ax2.set_ylim([15, 120])
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Ion current (nA)")
    ax2.set_yscale("log")
    ax2.set_ylim(bottom=0.05)
    #ax2.tick_params(axis='x', labelrotation=45, 'labelright')
    f1.autofmt_xdate()
    ax2.grid()

    if actions != None:
        # iterate over the actions and draw vertical grid lines on each plot
        for a in actions:
            dd = datetime.strptime(a[0], "%Y-%m-%d %I:%M%p")# convert to datetime
            ax1.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)
            ax2.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)

    if time_focus != None:# time focus is a start and end time to plot
        if time_focus[0] != None:
            left_time = datetime.strptime(time_focus[0], "%Y-%m-%d %I:%M%p")
            ax1.set_xlim(left=left_time)
        if time_focus[1] != None:
            right_time = datetime.strptime(time_focus[1], "%Y-%m-%d %I:%M%p")
            ax1.set_xlim(right=right_time)

    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()


def plot_all(data_p, data_I, time_focus = None, actions = None):

    # Prune data where the IG is off
    ii = np.less(data_p[:,1], 1e9)
    data_p = data_p[ii]

    tt_p = np.array([datetime.fromtimestamp(x) for x in data_p[:,0]])
    yy_p = data_p[:,1]

    # prune data where the ion pump is off
    #ii = np.greater(data_I[:,1], 0.1)# the ion pump set point can only go as low as 1.2 kV and is off for 0.0 kV.
    #data_I = data_I[ii]
    # change data with 0 nA current to be 0.1 nA and keep and index of these points.
    zeros_ii = np.less(data_I[:,2], 0.001)# < 0.001 nA and it can only output 0, 1, 2, ... nA.
    data_I[zeros_ii,2] = 0.1

    tt_I = np.array([datetime.fromtimestamp(x) for x in data_I[:,0]])
    yy_V = data_I[:,1]

    tt_I_on = tt_I[~zeros_ii]
    yy_I_on = data_I[~zeros_ii,2]

    tt_I_off = tt_I[zeros_ii]
    yy_I_off = data_I[zeros_ii,2]


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
    ax2.plot(tt_I_on, yy_I_on, '.', ms=2.0, color = "tab:blue", label = 'Ion pump I')
    ax2.plot(tt_I_off, yy_I_off, '.', ms=2.0, color = "tab:cyan", label = "Zero current")
    ax2.plot(tt_I, yy_V, '.', ms=2.0, color = "tab:orange", label = 'Ion pump V', zorder = -1)
    ax2.legend()
    #ax2.set_ylim([15, 120])
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Ion current (nA)")
    ax2.set_yscale("log")
    ax2.set_ylim(bottom=0.05)
    #ax2.tick_params(axis='x', labelrotation=45, 'labelright')
    f1.autofmt_xdate()
    ax2.grid()

    if actions != None:
        # iterate over the actions and draw vertical grid lines on each plot
        for a in actions:
            dd = datetime.strptime(a[0], "%Y-%m-%d %I:%M%p")# convert to datetime
            ax1.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)
            ax2.axvline(dd, color = 'C9', lw = 1.0, zorder=-1)

    if time_focus != None:# time focus is a start and end time to plot
        if time_focus[0] != None:
            left_time = datetime.strptime(time_focus[0], "%Y-%m-%d %I:%M%p")
            ax1.set_xlim(left=left_time)
        if time_focus[1] != None:
            right_time = datetime.strptime(time_focus[1], "%Y-%m-%d %I:%M%p")
            ax1.set_xlim(right=right_time)

    f1.canvas.draw_idle()# necessary to properly update the figure when reusing the same figure id.
    f1.show()


if __name__ == '__main__':

    path = "C:/Users/Amar Vutha/Documents/vutha_lab/cryoclock/pumping_manifold/"

    # Files for Dec 2023 bakeout and pumpout monitoring
    hornet_p_log_fn_list = [path+"hornet_pressure_logs/2023-12-13_hornet_p_log.txt",
                            path+"hornet_pressure_logs/2023-12-15_hornet_p_log.txt",
                            ]
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2023-12-13_nextorr_I_log.txt",
                             path+"nextorr_current_logs/2023-12-14_nextorr_I_log.txt",
                             path+"nextorr_current_logs/2023-12-15_nextorr_I_log.txt",
                         ]

    # Outgassing test 2024-01-10
    hornet_p_log_fn_list = [path+"hornet_pressure_logs/2024-01-10a_hornet_p_log.txt",
                            ]
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-01-10a_nextorr_I_log.txt",
                         ]

    # Close valve monitoring 2024-01-24
    hornet_p_log_fn_list = [path+"hornet_pressure_logs/2024-01-10a_hornet_p_log.txt",
                            ]
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-01-24_nextorr_I_log.txt",
                         ]

    # Turbo replacement pumpdown 2023-02-22
    hornet_p_log_fn_list = [path+"hornet_pressure_logs/2024-02-22_hornet_p_log.txt",
                            ]

    # Turn on rga filament
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-02-28_nextorr_I_log.txt",
                             path+"nextorr_current_logs/2024-03-01_nextorr_I_log.txt",
                             path+"nextorr_current_logs/2024-03-05_nextorr_I_log.txt",
                             path+"nextorr_current_logs/2024-03-07_nextorr_I_log.txt",
                         ]

    # After bakeout June 2024: 2024-06-20
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-06-20_nextorr_I_log.txt",
                         ]

    # After turning on NEG pump June 2024: 2024-06-24 to 2024-07-08
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-06-24_nextorr_I_log.txt",
                         ]


    # Rise-time outgassing meas July 2024: 2024-07-08
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-07-08_nextorr_I_log.txt",
                         ]


    # Pinchoff July 2024: 2024-07-23
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-07-23_nextorr_I_log.txt",
                         ]

    # Logging after pinchoff July 2024: 2024-07-25
    nextorr_I_log_fn_list = [path+"nextorr_current_logs/2024-07-25_nextorr_I_log.txt",
                         ]

    hornet_data_list = []
    for hornet_fn in hornet_p_log_fn_list:
        #print(hornet_fn)
        data = read_simple_hornet_p_log(hornet_fn)
        #print(f"data.shape: {data.shape}")
        hornet_data_list.append(data)
        #print(hornet_data_list)
    hornet_data = np.vstack(hornet_data_list)
    #print(hornet_data.shape)

    nextorr_data_list = []
    for hornet_fn in nextorr_I_log_fn_list:
        #print(hornet_fn)
        data = read_simple_nextorr_I_log(hornet_fn)
        #print(f"data.shape: {data.shape}")
        nextorr_data_list.append(data)
        #print(hornet_data_list)
    nextorr_data = np.vstack(nextorr_data_list)
    #print(hornet_data.shape)

    actions = [ ["2023-12-03 7:34PM", "Start of bake log spreadsheet."],
    ]

    time_focus = ["2023-12-13 8:00PM", None]
    time_focus = [None, None]

    #plot_p_log(hornet_data)

    plot_i_log(nextorr_data, time_focus)

    #plot_all(hornet_data, nextorr_data, time_focus)
