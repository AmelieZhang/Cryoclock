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


    hornet_p_log_fn_list = [path+"hornet_pressure_logs/2023-12-01b_hornet_p_log.txt",
                            #path+"hornet_pressure_logs/2023-12-02a_hornet_p_log.txt",
                            path+"hornet_pressure_logs/2023-12-02b_hornet_p_log.txt",
                            path+"hornet_pressure_logs/2023-12-03_hornet_p_log.txt",
                            ]
    tsp_T_log_fn_list = [path+"thorlabs_temperature_logs/2023-12-03_thorlabs_t_logs.txt",
                         path+"thorlabs_temperature_logs/2023-12-10_thorlabs_t_logs.txt",
                         path+"thorlabs_temperature_logs/2023-12-11_thorlabs_t_logs.txt",
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
                ["2023-12-03 7:47PM", "Set Variacs to 15V."],
                ["2023-12-03 8:02PM", "Set Variacs to 20 V."],
                ["2023-12-03 8:14PM", "Set variacs to 30, 25, 30 V"],
                ["2023-12-03 8:40PM", "Set variacs to 35, 30, 35"],
                ["2023-12-03 9:22PM", "Set variacs to 40, 35, 40"],
                ["2023-12-03 10:12PM", "Set variacs to 45, 40, 45 V"],
                ["2023-12-03 10:34PM", "Set variacs to 50, 42.5, 50 V"],
                ["2023-12-04 3:10PM", "Set variacs to 52.5, 45, 52.5 V. Also put more foil around the bottom of the IVC."],
                ["2023-12-04 3:33PM", "Set IVC variac to 47.5"],
                ["2023-12-04 3:52PM", "Set IVC variac to 50V. I also added a shield for the valve from the turbo fan."],
                ["2023-12-04 4:44PM", "Set IVC variac to 52.5V. Tried opening up the foil on the top of the cross some more."],
                ["2023-12-04 5:46PM", "Set IVC variac to 55 V. I also added more foil to the bottom of the IVC and the breadboard is is resting on."],
                ["2023-12-04 6:00PM", "Set Valve to 57.5 and RGA to 55 V."],
                ["2023-12-04 6:58PM", "Set valve to 60V and rga to 57.5V"],
                ["2023-12-04 7:55PM", "Set ivc variac to 57V (tried for 57 and not 57.5)"],
                ["2023-12-04 8:29PM", "Set ivc variac to 59 V"],
                ["2023-12-04 9:07PM", "Set ivc variac to 61V, Valve to 62.5V, rga to 60 V. While doing this I noticed that the 1.33CF valve is quite hot."],
                ["2023-12-04 9:38PM", "Set variacs to 65, 63, 62.5 V. Removed foil from top of cross, took pics."],
                ["2023-12-04 11:02PM", "Set IVC variac back to 61V in the interest of not overshooting 100C."],
                ["2023-12-05 1:31AM", "Set IVC variac to 59V just to be safe. I can't wait another 6 hours to see it plateau."],
                ["2023-12-05 1:54PM", "Set variacs to 67.5, 61, 65V"],
                ["2023-12-05 2:30PM", "Set ivc variac to 63V"],
                ["2023-12-05 3:11PM", "Set variacs to 70, 65, 67.5V. Wrapped more foil around the rga end."],
                ["2023-12-05 3:33PM", "Set variacs to 72.5, 67, 70V."],
                ["2023-12-05 4:47PM", "Set variacs to 75, 69, 72.5V. Put more aluminum foil around the end of the 2.75CF valve."],
                ["2023-12-05 8:12PM", "Set ivc variac to 67.5V since it was more like 68.5V already. Play it safe."],
                ["2023-12-06 11:40AM", "Set variacs to 77.5, 70, 75V."],
                ["2023-12-06 12:55PM", "Set ivc variac to 70 plus a quarter of a division."],
                ["2023-12-06 1:49PM", "Set rga variac to 77.5V. ALso tried to tape down the foil on the back of the IVC better. Not sure better."],
                ["2023-12-06 5:29PM", "Increased ivc by 1/8 div to 70V+3/8*5V, Increased rga and valve by 1/4 div to 75+3/4*5V."],
                ["2023-12-07 12:45PM", "Set Hornet from 100 uA to 4 mA emission current."],
                ["2023-12-07 3:33PM", "Set Hornet to 100 uA emis curr setting."],
                ["2023-12-07 8:13PM", "Put one long foil along rga arm, then one short on the end. Cross foil is not as bent back in all directions now."],
                ["2023-12-07 8:35PM", "Bent back aluminium foil on cross to how it was before I added the rga foil."],
                ["2023-12-08 1:34PM", "Put aluminum foil on the vertical support 8020 next to the valve. Curiosity. Finsihed about 145pm."],
                ["2023-12-10 6:12PM", "I restarted the Thorlabs T log. The 45 min or so before that I was fixing it."],
                ["2023-12-11 1:42PM", "Reset T log to be 10 s instead of 30 s invervals while cooling down."],
                ["2023-12-11 1:46PM", "Set rga and valve variacs to 75V"],
                ["2023-12-11 2:30PM", "Reduce rga and valve to 70V"],
                ["2023-12-11 3:55PM", "Reduced rga and valve varaics to 65V"],
                ["2023-12-11 5:08PM", "Reduced rga and valve variacs to 60V"],
                ["2023-12-11 5:51PM", "Reduced variacs to 57.5, 70, 57.5V"],
                ["2023-12-11 6:27PM", "Reduced ivc variac to 67.5V"],
                ["2023-12-11 7:52PM", "Reduced variacs to 55, 62.5, 55V"],
                ["2023-12-11 8:46PM", "Reduced variacs to 52.5, 57.5, 52.5V. I waffled and changed them for a couple of minutes."],
                ["2023-12-11 10:44PM", "Reduced variacs to 50, 55, 50V"],
                ["2023-12-11 10:48PM", "Reduced variacs to 47.5, 52.5, 47.5V. Loosened foil around bellows a bit. Took pics."],
                ["2023-12-12 9:59AM", "Reduce each variac by 7.5 V to 40,45,40V"],
                ["2023-12-12 11:46AM", "Reduce variacs to 37.5, 40, 37.5"],
                ["2023-12-12 1:15PM", "Reduce variacs to 32.5, 37.5, 32.5 V"],
                ["2023-12-12 1:59PM", "Reduce variacs to 27.5, 35.0, 27.5V"],
                ["2023-12-12 2:31PM", "Reduce variacs to 22.5, 27.5, 22.5V"],
                ["2023-12-12 2:47PM", "Removed some alumium foil from the IVC and valve."],
                ["2023-12-12 2:57PM", "Reduced variacs to 17.5, 22.5, 17.5V"],
                ["2023-12-12 4:13PM", "Reduced variacs to 12.5, 17.5, 12.5V"],
                ["2023-12-12 4:40PM", "Removed all outer foil from IVC. Heater tape and inner foil layers still on."],
                ["2023-12-12 4:57PM", "Reduced variacs to 0, 17.5, 0V (and turned off 0V ones)"],
                ["2023-12-12 6:12PM", "Reduced ivc variac to 0V. All variacs are off now."],
                ["2023-12-12 6:41PM", "Removed heater tape from IVC. As well as some of the inner foil under it. Took about 10 min."],
                ["2023-12-12 6:55PM", "Removed all but about 1 or 1.5 layers of Al foil from the IVC."],
                ["2023-12-12 7:00PM", "Removed foil from RGA arm and attached RGA electronics."],
                ["2023-12-12 7:23PM", "Turned on RGA filament."],
                ["2023-12-12 7:48PM", "Removed the last of the foil around the IVC"],
    ]

    #plot_p_log(hornet_data)
    #plot_T_log(tsp_data)
    #plot_dTdt(tsp_data)

    plot_p_and_T(hornet_data, tsp_data, actions)
    #plot_p_and_T(hornet_data, tsp_data)
