import numpy as np 
import matplotlib.pyplot as plt 
from preprocessing import scale, remove_elevation_azimuth_structures, remove_spikes
import h5py
import julian
import matplotlib

font = {'size'   : 15}

matplotlib.rc('font', **font)

#colors = ['#173F5F', '#7ea3be', '#20639b', '#b1cce1', '#3caea3', '#a1d8d2', '#f6d55c', '#faedc0','#ed553b', '#f2c1ba']
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
colors = colors + colors

def read_file(filename):
    month = filename[14:21]
    obsid = int(filename[7:13])

    # Reading in relevant information from file     
    path = '/mn/stornext/d16/cmbco/comap/pathfinder/ovro/' + month + '/'
    with h5py.File(path + filename, 'r') as hdf:
        try:
            tod        = np.array(hdf['spectrometer/band_average'])
            el         = np.array(hdf['/spectrometer/pixel_pointing/pixel_el'])
            az         = np.array(hdf['/spectrometer/pixel_pointing/pixel_az'])
            features   = np.array(hdf['spectrometer/features'])
            mjd        = np.array(hdf['spectrometer/MJD'])
            feeds      = np.array(hdf['spectrometer/feeds'])
            MJD_start  = float(hdf['spectrometer/MJD'][0])
            attributes = hdf['comap'].attrs
            target     = attributes['source'].decode()
        except:
            print('Not sufficient information in the level 1 file')

    # Removing Tsys measurements    
    boolTsys = (features & 1 << 13 != 8192)
    indexTsys = np.where(boolTsys == False)[0]

    if len(indexTsys) > 0 and (np.max(indexTsys) - np.min(indexTsys)) > 5000:
        boolTsys[:np.min(indexTsys)] = False
        boolTsys[np.max(indexTsys):] = False

    tod       = tod[:,:,boolTsys]
    el        = el[:,boolTsys]
    az        = az[:,boolTsys]
    mjd       = mjd[boolTsys]
    
    # Removing NaNs          
    for feed in range(np.shape(tod)[0]):
        for sideband in range(np.shape(tod)[1]):
            if np.isnan(tod[feed, sideband]).all():
                tod[feed,sideband] = 0

    mask = np.isnan(tod)
    tod[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), tod[~mask])

    
    return tod, mjd, el, az, feeds, obsid

def plot_whole_tod(filename):
    # Calculating subsequence length 
    fs = 50
    T = 1/fs
    subseq_length = int(10*60/T)

    tod, mjd, el, az, feeds, obsid = read_file(filename)
    
    time = []
    for i in range(len(mjd)):
        time.append(julian.from_jd(mjd[i], fmt='mjd'))


    """
    obsid, feed, sideband, width, ampl, index, mjd, mjd_start = np.loadtxt('data/spike_data/spike_list.txt', skiprows=1, unpack=True)
    print(obsid)

    index = index.astype(int)

    plt.figure()
    plt.plot(tod_old[0,0])
    for i in range(len(obsid)):
        if feed[i] == 1 and sideband[i] == 1:
            print(index[i], width[i], ampl[i])
            plt.plot(index[i]+1, tod_old[0,0][index[i]+1], 'mo')
    plt.show()
    """


    tod_new = tod #np.nanmean(tod, axis=1)
    max_y = np.max(tod_new[:-1])*1.15  
    min_y = np.min(tod_new[:-1])  - (np.max(tod_new[:-1])*0.01)                   

    fig = plt.figure(figsize=(11,5))
    ax = fig.add_subplot(111)
    hours = matplotlib.dates.MinuteLocator(interval = 10)
    h_fmt = matplotlib.dates.DateFormatter('%H:%M:%S')
                          
    for feed in range(np.shape(tod_new)[0]-1):
        for sideband in range(np.shape(tod_new)[1]):
            if np.sum(tod_new[feed,sideband]) == 0:
                continue
            plt.plot(time, tod_new[feed,sideband], linewidth=0.8, color = colors[feed], label='Feed: %d, Sideband: %d' %(feeds[feed], sideband))

    #plt.legend()
    for i in range(int(np.shape(tod_new)[-1])//30000 + 1):
        try:
            plt.axvline(time[i*subseq_length], color='black', alpha=0.5)
            if i != int(np.shape(tod_new)[-1])//30000:
                plt.text(time[i*subseq_length+int(subseq_length/2)], max_y*0.85, '%d' %(i+1), alpha=0.5)
        except:
            pass
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
                                                                                                 
    plt.xlabel('UTC (hours)')
    plt.ylabel('Power')
    plt.ylim(min_y,max_y)
    fig.autofmt_xdate()
    #plt.tight_layout()                                                                                     
    plt.title('ObsID: %s' %obsid)
    plt.savefig('figures/%d_whole_tod.pdf' %obsid, bbox_inches = "tight")
    plt.show()

    


def plot_subsequence(filename, subseq=False):
    # Calculating subsequence length                            
    fs = 50
    T = 1/fs
    subseq_length = int(10*60/T)

    if subseq:
        index1 = subseq_length*(subseq-1)
        index2 = subseq_length*subseq
    else:
        filename = line.split()[0]
        index1 = int(line.split()[1])
        index2 = int(line.split()[2])
        index = (index1, index2)
        subseq = int(index2/30000)

    tod, mjd, el, az, feeds, obsid = read_file(filename)

    # Extracting subsequence 
    tod       = tod[:,:,index1:index2]
    el        = el[:,index1:index2]
    az        = az[:,index1:index2]
    mjd       = mjd[index1:index2]


    time = []
    for i in range(len(mjd)):
        time.append(julian.from_jd(mjd[i], fmt='mjd'))


    tod_new = tod

    fig = plt.figure(figsize=(5,4))
    ax = fig.add_subplot(111)
    hours = matplotlib.dates.MinuteLocator(interval = 2)
    h_fmt = matplotlib.dates.DateFormatter('%H:%M:%S')
                          
    for feed in range(np.shape(tod_new)[0]-1):
        for sideband in range(np.shape(tod_new)[1]):
            if np.sum(tod_new[feed,sideband]) == 0:
                continue
            plt.plot(time, tod_new[feed,sideband], linewidth=0.8, color = colors[feed], label='Feed: %d, Sideband: %d' %(feeds[feed], sideband))


    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
                                                                                                 
    plt.xlabel('UTC (hours)')
    plt.ylabel('Power')
    fig.autofmt_xdate()
    plt.grid()
    plt.title('ObsID: %s' %obsid)
    plt.savefig('figures/%d_subseq_%d_scaled.pdf' %(obsid, subseq), bbox_inches = "tight")
    plt.show()


def plot_az_el_removal(filename, subseq=False):
    # Calculating subsequence length                            
    fs = 50
    T = 1/fs
    subseq_length = int(10*60/T)

    if subseq:
        index1 = subseq_length*(subseq-1)
        index2 = subseq_length*subseq
    else:
        filename = line.split()[0]
        index1 = int(line.split()[1])
        index2 = int(line.split()[2])
        index = (index1, index2)
        subseq = int(index2/30000)

    tod, mjd, el, az, feeds, obsid = read_file(filename)

    # Extracting subsequence 
    tod       = tod[:,:,index1:index2]
    el        = el[:,index1:index2]
    az        = az[:,index1:index2]
    mjd       = mjd[index1:index2]

    time = []
    for i in range(len(mjd)):
        time.append(julian.from_jd(mjd[i], fmt='mjd'))
    
    
    feed = 0
    sideband = 0

    fig = plt.figure(figsize=(11,3))

    plt.subplot(1,2,1)
    plt.plot(tod[feed,sideband], linewidth=0.8, label=r'$d_{before}$')
    plt.xlabel('Sample')
    plt.ylabel('Power')
    plt.grid()
    plt.ylim(top=np.max(tod[feed,sideband])*1.001)

    tod_new = remove_elevation_azimuth_structures(tod, el, az, plot=True)
    tod_new = tod_new[feed,sideband]
    plt.legend(prop={'size': 12})
    
    plt.subplot(1,2,2)
    plt.plot(tod_new, label=r'$d_{after}$')
    plt.xlabel('Sample')
    plt.ylabel('Power')
    plt.grid()
    plt.tight_layout()
    plt.suptitle('ObsID: %s' %obsid, y=1.05)
    plt.savefig('figures/%d_subseq_%d_%d_%d_remove_az_el.pdf' %(obsid, subseq, feed, sideband), bbox_inches = "tight")
    plt.legend(prop={'size': 12})
    plt.ylim(top=np.max(tod[feed,sideband])*1.001)
    plt.show()


def plot_scaled(filename, subseq=False):
    # Calculating subsequence length                            
    fs = 50
    T = 1/fs
    subseq_length = int(10*60/T)

    if subseq:
        index1 = subseq_length*(subseq-1)
        index2 = subseq_length*subseq
    else:
        filename = line.split()[0]
        index1 = int(line.split()[1])
        index2 = int(line.split()[2])
        index = (index1, index2)
        subseq = int(index2/30000)

    tod, mjd, el, az, feeds, obsid = read_file(filename)

    # Extracting subsequence 
    tod       = tod[:,:,index1:index2]
    el        = el[:,index1:index2]
    az        = az[:,index1:index2]
    mjd       = mjd[index1:index2]

    time = []
    for i in range(len(mjd)):
        time.append(julian.from_jd(mjd[i], fmt='mjd'))
    

    tod_new = remove_elevation_azimuth_structures(tod, el, az) 
    tod_new = scale(tod_new)

    fig = plt.figure(figsize=(5,4))
    plt.plot(tod_new)
    plt.xlabel('Sample')
    plt.ylabel('Power')
    plt.ylim(-0.1,0.1)
    plt.grid()
    plt.title('ObsID: %s' %obsid)
    plt.savefig('figures/%d_subseq_%d_scaled_same_y.pdf' %(obsid, subseq), bbox_inches = "tight")
    plt.show()


    
# 'comap-0010402-2020-01-10-225243.hd5', 'comap-0006801-2019-07-09-005158.hd5', 'comap-0006819-2019-07-10-230632.hd5'
filenames = ['comap-0007343-2019-08-07-220019.hd5', 'comap-0007368-2019-08-09-041820.hd5',  'comap-0008210-2019-10-08-095538.hd5']
#plot_whole_tod(filenames[0])
#plot_subsequence(filenames[1], 1)
#plot_az_el_removal(filenames[-1],1)
plot_scaled(filenames[1],1)