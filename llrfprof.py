""" used to profile llrf """
from __future__ import print_function
import sys
import argparse

import numpy as np
from six.moves import input
from interfaces import SocketInterface, TempPrologixEnetInterface
from specanalyzer import RandSFSP
from bncinst import BNC845

from adcutils import which_channel, gen_filename, adc_vals

GEN_ADDR = ('131.243.171.52', 18)
GEN_MIN = -30
GEN_MAX = 15
FREQ = 185.7E6
SPAN = .03E6
POINTS = 91
ROW_FORMAT = " ".join(["{" + str(i) + ":>10f}" for i in range(4)]) + '\n'


def main(args):
    """ runs either profile or measure channel after asking for correct channel """
    channel = which_channel()

    if args.profile:
        profile(args, channel)
        sys.exit(0)

    measure_channel(args, channel)

def measure_channel(args, channel):
    """ measures channel output for inputs from min to max """
    if inputs_ok(args.min, args.max) != 'Y':
        sys.exit(0)
    gen = init_gen(args.min, args.max, channel.gain_file)
    inputs = np.linspace(args.min, args.max, num=args.points, endpoint=True)
    with open("data/" + gen_filename(channel.name), 'w+') as data_file:
        gen.power_sweep(inputs, output_callback, (channel.adc, data_file), delay=.1)

def init_spec():
    """ returns initialized spectrum analyzer """
    interface = TempPrologixEnetInterface(18, ("131.243.171.57", 1234))
    spec = RandSFSP(interface)
    spec.timeout = 30000
    spec.query_delay = 0
    spec.rst()
    spec.continuous_sweep = False
    spec.display_on(False)
    spec.set_window(FREQ, SPAN)
    return spec

def init_gen(min_output, max_output, gain_file=None):
    """ returns initialized signal generator """
    interface = SocketInterface(("131.243.171.52", 18))
    gen = BNC845(interface, min_output=min_output, max_output=max_output, gain_file=gain_file)
    gen.signal_on = False
    return gen

def output_callback(raw_power, real_power, state):
    """ callback to output raw data """
    adc, data_file = state
    adc_min, adc_max = adc_vals(adc)
    print(ROW_FORMAT.format(raw_power, real_power, adc_min, adc_max))
    data_file.write(ROW_FORMAT.format(raw_power, real_power, adc_min, adc_max))


def profile(args, channel):
    """ profile generator for specified channel """
    gen = init_gen(args.min, args.max)
    spec = init_spec()
    attn = -20 if int(channel.gain_file.lstrip("BNC_AMP")[:1]) != 0 else 0
    if channel.gain_file == 'BNC_AMP30_ATN-20':
        attn = 0
    output_powers = np.linspace(args.min, args.max, 81)
    gen.profile(channel.gain_file, output_powers, lambda: spec.get_peak() - attn, runs=3)
def inputs_ok(low, high):
    """ ask for confirmation that inputs are alright """
    print("Input Low: " + str(low) + "\nInput High: " +
          str(high))
    return input("Are these inputs ok? [Y/n]: ")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile llrf1")
    parser.add_argument("min", type=float, help="Min signal power (dbm)")
    parser.add_argument("max", type=float, help="Max signal power (dbm)")
    parser.add_argument("-p", "--points", type=int, default=101, help="Number of data points to take")
    parser.add_argument("--profile", help="Profile selected channel", action="store_true")
    _ARGS = parser.parse_args()
    main(_ARGS)
