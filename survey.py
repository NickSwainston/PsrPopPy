#!/usr/bin/python

import os
import sys

#import ephem
import math
import random

from galacticops import GalacticOps
from population import Population

class Survey(GalacticOps):
    """Class to store survey parameters and methods"""
    def __init__(self, surveyName):
        """Read in a survey file and obtain the survey parameters"""
        try:
            # get path to surveys directory
            __dir__ = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(__dir__, 'surveys', surveyName)
            f = open(filepath, 'r')
        except IOError:
            print 'No such file: ',surveyName
            sys.exit()

        self.surveyName = surveyName
        # Parse the file line by line
        for line in f.readlines():
            # ignore any lines starting '#'
            if line.strip()[0] == '#':
                continue
            # otherwise, parse!
            a = line.split('!')
            
            if a[1].count('survey degradation'):
                # beta
                self.beta = float(a[0].strip())
            elif a[1].count('gain'):
                # gain
                self.gain = float(a[0].strip())
            elif a[1].count('integration time'):
                # tobs
                self.tobs = float(a[0].strip())
            elif a[1].count('sampling'):
                # tsamp
                self.tsamp = float(a[0].strip())
            elif a[1].count('system temperature'):
                # tsys
                self.tsys = float(a[0].strip())
            elif a[1].count('centre frequency'):
                # centre frequency
                self.freq = float(a[0].strip())
            elif a[1].strip().startswith('bandwidth'):
                # bandwidth
                self.bw = float(a[0].strip())
            elif a[1].count('channel bandwidth'):
                # bw_chan
                self.bw_chan = float(a[0].strip())
            elif a[1].count('polarizations'):
                # num polns
                self.npol = float(a[0].strip())
            elif a[1].count('half maximum'):
                # FWHM
                self.fwhm = float(a[0].strip())
            elif a[1].count('minimum RA'):
                # min RA
                self.RAmin = float(a[0].strip())
            elif a[1].count('maximum RA'):
                # max RA
                self.RAmax = float(a[0].strip())
            elif a[1].count('minimum DEC'):
                # min dec
                self.DECmin = float(a[0].strip())
            elif a[1].count('maximum DEC'):
                # mac dec
                self.DECmax = float(a[0].strip())
            elif a[1].count('minimum Galactic'):
                # min longitude
                self.GLmin = float(a[0].strip())
            elif a[1].count('maximum Galactic'):
                # max longitude
                self.GLmax = float(a[0].strip())
            elif a[1].count('minimum abs'):
                # min latitude
                self.GBmin = float(a[0].strip())
            elif a[1].count('maximum abs'):
                # max latitude
                self.GBmax = float(a[0].strip())
            elif a[1].count('survey coverage'):
                # coverage fraction
                self.coverage = float(a[0].strip())
                if self.coverage > 1.0:
                    self.coverage = 1.0
            elif a[1].count('signal-to-noise'):
                # SNR limit
                self.SNRlimit = float(a[0].strip())

            else:
                print "Parameter ",a[1].strip()," not recognized!"
    
    def __str__(self):
        """Method to define how to print the class"""
        s = "Survey class for {0}:".format(self.surveyName)
        s = '\n\t'.join([s, "beta = {0}".format(self.beta)])
        s = '\n\t'.join([s, "gain = {0}".format(self.gain)])
        s = '\n\t'.join([s, "tobs = {0} s".format(self.tobs)])
        s = '\n\t'.join([s, "tsamp = {0} ms".format(self.tsamp)])
        s = '\n\t'.join([s, "Tsys = {0} K".format(self.tsys)])
        s = '\n\t'.join([s, "Centre frequency = {0} MHz".format(self.freq)])
        s = '\n\t'.join([s, "Bandwidth = {0} MHz".format(self.bw)])
        s = '\n\t'.join([s, "Chan BW = {0} MHz".format(self.bw_chan)])
        s = '\n\t'.join([s, "Num polarisations = {0}".format(self.npol)])
        s = '\n\t'.join([s, "FWHM = {0} arcmin".format(self.fwhm)])
        s = '\n\t'.join([s, "SNR limit = {0}".format(self.SNRlimit)])

        return s

    #@Property
    def nchans(self):
        return self.bw / self.bw_chan
    """
        def fset(self):
            self.result =  self.bw / self.bw_chan
        def fget(self):
            return self.result
        return locals()
        """


    def inRegion(self, pulsar):
        """Test if pulsar is inside region bounded by survey"""
        # check if l, b are outside region first of all
        if pulsar.gl > self.GLmax or pulsar.gl < self.GLmin:
            return False
        if math.fabs(pulsar.gb) > self.GBmax or  math.fabs(pulsar.gb) < self.GBmin:
            return False

        # need to compute ra/dec of pulsar from the l and b (galtfeq)
        ra, dec = self.lb_to_radec(pulsar.gl, pulsar.gb)

        # are ra, dec outside region?
        if ra > self.RAmax or ra < self.RAmin:
            return False
        if dec > self.DECmax or dec < self.DECmin:
            return False
        
        # randomly decide if pulsar is in completed area of survey
        if random.random() > self.coverage:
            return False
        
        return True


    def SNRcalc(self, pulsar, pop):
        # if not in region, S/N = 0
        if self.inRegion(pulsar):
            pass
        else:
            return -2.0

        # calculate offset as a random offset within FWHM/2
        # why is this a sqrt???
        offset = self.fwhm * math.sqrt(random.random()) / 2.0
        degfac = math.exp(-2.7726 * offset * offset / (self.fwhm *self.fwhm))

        # don't think I need to do this - I'm using the survey freq in call
        Ttot = self.tsys + self.tsky(pulsar.gl, pulsar.gb, self.freq)

        # calc dispersion smearing across single channel
        tdm = self._dmsmear(pulsar)

        # calculate bhat et al scattering time (inherited from GalacticOps)
        # in units of ms
        tscat = self.scatter_bhat(pulsar.dm, pulsar.scindex, self.freq)

        # Calculate the effective width
        weff_ms = math.sqrt(pulsar.width_ms()**2 + self.tsamp**2 + tdm**2 + tscat**2)

        # calculate duty cycle (period is in ms)
        delt = weff_ms / pulsar.period

        # if pulse is smeared out, return -1.0
        if delt > 1.0:
            #print weff_ms, tscat, pulsar.dm, pulsar.gl, pulsar.gb, pulsar.dtrue
            return -1.0
        else:
            return self._SNfac(pulsar, pop.ref_freq, degfac, Ttot) * math.sqrt((1.0 -delt)/delt)

    def _SNfac(self, pulsar, ref_freq, degfac, Ttot):
        # scale flux to survey frequency
        flux = pulsar.s_1400() * (self.freq / ref_freq)**pulsar.spindex

        return pulsar.s_1400() * degfac * self.gain * \
                  math.sqrt(self.npol * self.bw * self.tobs) \
                  / self.beta / Ttot

    def _dmsmear(self, pulsar):
        return 8.3E6 * pulsar.dm * self.bw_chan / math.pow(self.freq, 3.0)