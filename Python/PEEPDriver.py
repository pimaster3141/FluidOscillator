import time;
import math; 

class PEEPDriver(threading.Thread):

    PEEP_UPDATE_PERIOD = 0.5;

    def __init__(self, eagle, amplitude, baseline, cycles, frequency):
        threading.Thread.__init__(self);

        self.EMV = eagle;
        self.amplitude = amplitude;
        self.baseline = baseline;
        self.cycles = cycles;
        self.frequency = frequency;

        self.isAlive = True;

    def run(self):
        while(isAlive):
            


