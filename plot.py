import os
import numpy as np
import pandas as pd
from adcutils import CHANNELS
from matplotlib import pyplot as plt
if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')

SATURATED = 32764

def most_current(prefix, directory='./data'):
    files = [filename for filename in os.listdir(directory)
             if filename[0:len(prefix)] == prefix]
    if files:
        return files.pop()


def read_data(filename, channel):
    assert filename
    names = ['raw_input', 'real_input', 'adc_min', 'adc_max']
    data = pd.read_csv(filename, delim_whitespace=True, header=None, names=names, index_col=1)
    data.name = channel.name.replace(' ', '_')
    data['measured_power'] = 20 * np.log10((data.adc_max - data.adc_min) / 65536.)
    return data


def plot_scatter_fit(data, ax):
    data.plot(label='channel response', marker='o', ls='None', ax=ax)
    z = np.polyfit(x=data.keys(), y=data, deg=3)
    p = np.poly1d(z)
    ax.plot(data.keys(), p(data.keys()), c='orange', ls='-', label='best fit')

    fit = 'a0 = {3:>.2E}, a1 = {2:>.2E}, a2 = {1:>.2E}, a3 = {0:>.2E}'.format(
        *z)
    ax.annotate(fit, xy=(.05, .05), xycoords='axes fraction')
    sat_pt = "Saturation {:.2f} dBm".format(data.idxmax())
    ax.annotate(sat_pt, xy=(data.idxmax(), data.max()), xycoords='data',
                xytext=(data.idxmax() - 0, data.max() - 10), textcoords='data',
                arrowprops=dict(facecolor='black', shrink=.05),
                horizontalalignment='right', verticalalignment='top')
    return ax

def adc_to_power(adc_min, adc_max):
    return 20 * np.log10((adc_max - adc_min) / 65536.)

def saturation_point(data):
    """
    returns the input value that the channel reading saturated
    """
    sat_adc_min = data.adc_min.idxmin() if abs(data.adc_min.min()) >= SATURATED else None
    sat_adc_max = data.adc_max.idxmax() if data.adc_max.max() >= SATURATED else None
    if sat_adc_min is None or sat_adc_max is None:
        return None
    return min(sat_adc_min, sat_adc_max)

def get_data(channel):
    """
    returns all data for a given channel that contains the saturation point and
    a range of at least 15 dBm of input
    """
    directory = './data'
    prefix = channel.name.replace(' ', '_')
    filenames = [filename for filename in os.listdir(directory) if filename.startswith(prefix)]
    raw_data = {filename: read_data(directory + '/' + filename, channel) for filename in filenames}
    for filename, data in raw_data.iteritems():
        if saturation_point(data) is not None:
            dbm_range = data.index.max() - data.index.min()
            if dbm_range < 3:
                print(filename + ' Saturation = ' + str(saturation_point(data)))

    useful_data = {filename: data[:saturation_point(data)] for (filename, data) in raw_data.iteritems()
                   if data.index.max() - data.index.min() > 15 and
                   saturation_point(data) is not None}

    return useful_data

def plot_measured_and_gain(channel, powers):
    """ plots the measured channel response and gain on two separate axes """
    plt.figure(figsize=(7, 9.5))
    ax = plt.subplot(211)
    plot_scatter_fit(powers, ax)
    ax.set_xlabel('Power input (dBm)')
    ax.set_ylabel('Measured input (dBm)')
    ax.set_title('Measured Input vs Input')
    ax.legend(loc='best')

    gains = powers - powers.keys()
    ax = plt.subplot(212)
    gains.plot(ax=ax, marker='o', ls='None', label='channel gains')

    ax.set_xlabel('Power input (dBm)')
    ax.set_ylabel('Gain (dBm)')
    ax.set_title('Measured Gain vs Input')
    plt.suptitle('llrf1 ' + channel.name)

def main():
    for channel in CHANNELS:
        chan_data = get_data(channel)
        for filename, data in chan_data.iteritems():
            plot_measured_and_gain(channel, data.measured_power)
            plt.savefig("plots/" + filename + ".png")
            plt.clf()


if __name__ == '__main__':
    main()
    