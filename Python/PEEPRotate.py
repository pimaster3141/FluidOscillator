import time;
import math; 

class PEEPRotate(threading.Thread):

	PEEP_UPDATE_PERIOD = 0.5;

	def __init__(self, eagle, amplitude, baseline, cycles, frequency):
		threading.Thread.__init__(self);

		self.EMV = eagle;
		self.amplitude = amplitude;
		self.baseline = baseline;
		self.cycles = cycles;
		self.frequency = frequency;

		self.isAlive = True;
		self.start();
		return;

	def run(self):
		self.startTime = time.time();
		self.EMV.sendPulse();

		while(self.isAlive):
			if(time.time()-self.startTime < self.cycles/self.frequency):
				loopTime = time.time();
				peepUpdate = self.amplitude * math.sin(2*math.pi * self.frequency) + self.baseline;
				self.EMV.setPEEP(peepUpdate);
				time.sleep(PEEPDriver.PEEP_UPDATE_PERIOD - (time.time() - startTime));
			else:
				self.isAlive = False;
				self.EMV.setPEEP(self.baseline);
				self.EMV.sendPulse();
		return;
		
	def stepsRemaining(self):
		if(self.isAlive):
			remaining  = self.cycles - (time.time()-self.startTime)*self.frequency;
			return(max(0, remaining));
		else:
			return 0;

	def stop(self):
		self.isAlive = False;
		self.join();
		return;


