import time;
import math; 
import threading;

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
		self.startTime = time.clock();
		self.EMV.sendPulse();

		while(self.isAlive):
			if(time.clock()-self.startTime < self.cycles/self.frequency):
				loopTime = time.clock();
				waveTime = time.clock() - self.startTime;
				peepUpdate = self.amplitude * math.sin(2*math.pi * waveTime * self.frequency) + self.baseline;
				self.EMV.setPEEP(peepUpdate);
				#print(round(peepUpdate, 1));
				#print(round(waveTime, 1));
				# print(self.startTime);
				#print();
				# time.sleep(max(PEEPRotate.PEEP_UPDATE_PERIOD - (time.clock() - loopTime)), 0);
				time.sleep(PEEPRotate.PEEP_UPDATE_PERIOD);
			else:
				self.isAlive = False;
				self.EMV.setPEEP(self.baseline);
				self.EMV.sendPulse();
		return;
		
	def stepsRemaining(self):
		if(self.isAlive):
			remaining  = self.cycles - (time.clock()-self.startTime)*self.frequency;
			return(max(0, remaining));
		else:
			return 0;

	def stop(self):
		self.isAlive = False;
		self.join();
		return;


