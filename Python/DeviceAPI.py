import EagleDriver;
import StepperDriver;

class DeviceAPI():


	# devID:	[0-motor
	#			 1-25ml Pump
	#			 2-2.5ml Pump
	#			 3-EMV]
	def __init__(self, motorCOM, devID, emvCOM=None):
		if(devID == 3 && emvCOM == None):
			raise Exception("No EMV COM Specified");

		self.motorCOM = motorCOM;
		self.emvCOM = emvCOM;
		self.device = devID;

		return;

	def __delete__(self):
		self.close();
		return;

	def close(self):
		return;

	def sendPulse(self):
		
		return;

	# Frequency(Hz)
	# Amplitude(ml -or- mmHg) (NOT PEAK-PEAK)
	def rotate(self, direction, frequency, amplitude, rotations):
		return;

	# motor/pump - offset by ml or angle
	# EMV - set PEEP to value;
	def offset(self, offset):
		return;

	def isRunning():
		return True;

	def percentRemaning(steps=100):
		return steps;

