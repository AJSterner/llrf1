""" useful functions for adc measurements """
from __future__ import print_function
from time import localtime
from collections import namedtuple
import warnings

Channel = namedtuple('Channel', ['name', 'adc', 'nominal', 'gain_file'])
CHANNELS = [Channel(name='Cavity Cell Voltage', adc='adc4', nominal=26, gain_file='BNC_AMP30_ATN-0'),
            Channel(name='REV Cavity', adc='adc3', nominal=15, gain_file='BNC_AMP30_ATN-10'),
            Channel(name='FWD Cavity', adc='adc2', nominal=15, gain_file='BNC_AMP30_ATN-10'),
            Channel(name='Laser Cavity', adc='adc1', nominal=-27, gain_file='BNC_AMP0_ATN-26'),
            Channel(name='Laser after amp', adc='adc1', nominal=10, gain_file='BNC_AMP30_ATN-20')]

try:
    from epics import caget
    from epics.ca import ChannelAccessException
    try:
        for channel in CHANNELS:
            adc_vals(channel.adc)
    except ChannelAccessException:
        warnings.warn("Cannot find EPICS CA DLL, make sure to set PATH")
except ImportError:
    warnings.warn("Could not import pyepics")

def adc_vals(channel):
    """ returns tuple containing adc_min and adc_max for given channel """
    adc_min = float(caget('llrf1:' + channel + '_min'))
    adc_max = float(caget('llrf1:' + channel + '_max'))
    return adc_min, adc_max

def which_channel():
    """ command line prompt for choosing channel """
    for i, channel in enumerate(CHANNELS):
        print('[' + str(i) + '] ' + channel.name)
    try:
        channel = CHANNELS[int(input('Enter number of channel: '))]
    except ValueError:
        print('\nPlease enter a valid channel number')
        channel = which_channel()

    return channel

def gen_filename(prefix):
    """ generates filename: channel_name"""
    filename = prefix.replace(' ', '_')
    currtime = localtime()
    for i in range(5):
        filename += '-' + str(currtime[i])
    return filename



