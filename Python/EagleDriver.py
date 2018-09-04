import serial;
import threading;
from threading import Lock;
import time;
import PEEPRotate;

class EagleDriver(threading.Thread):
	CRC_TABLE = [0, 145, 97, 240, 194, 83, 163, 50, 199, 86, 166, 55, 5, 148, 100, 245,
				205, 92, 172, 61, 15, 158, 110, 255, 10, 155, 107, 250, 200, 89, 169, 56,
				217, 72, 184, 41, 27, 138, 122, 235, 30, 143, 127, 238, 220, 77, 189, 44,
				20, 133, 117, 228, 214, 71, 183, 38, 211, 66, 178, 35, 17, 128, 112, 225,
				241, 96, 144, 1, 51, 162, 82, 195, 54, 167, 87, 198, 244, 101, 149, 4,
				60, 173, 93, 204, 254, 111, 159, 14, 251, 106, 154, 11, 57, 168, 88, 201,
				40, 185, 73, 216, 234, 123, 139, 26, 239, 126, 142, 31, 45, 188, 76, 221,
				229, 116, 132, 21, 39, 182, 70, 215, 34, 179, 67, 210, 224, 113, 129, 16,
				161, 48, 192, 81, 99, 242, 2, 147, 102, 247, 7, 150, 164, 53, 197, 84,
				108, 253, 13, 156, 174, 63, 207, 94, 171, 58, 202, 91, 105, 248, 8, 153,
				120, 233, 25, 136, 186, 43, 219, 74, 191, 46, 222, 79, 125, 236, 28, 141,
				181, 36, 212, 69, 119, 230, 22, 135, 114, 227, 19, 130, 176, 33, 209, 64,
				80, 193, 49, 160, 146, 3, 243, 98, 151, 6, 246, 103, 85, 196, 52, 165,
				157, 12, 252, 109, 95, 206, 62, 175, 90, 203, 59, 170, 152, 9, 249, 104,
				137, 24, 232, 121, 75, 218, 42, 187, 78, 223, 47, 190, 140, 29, 237, 124,
				68, 213, 37, 180, 134, 23, 231, 118, 131, 18, 226, 115, 65, 208, 32, 177]

	# HOST_ENABLE_CMD = 0xF13BD08C;
	HOST_ENABLE_CMD = [0x02, 0xf5, 0x33, 0x20, 0x46, 0x31, 0x33, 0x42, 0x44, 0x30, 0x38, 0x43, 0x20, 0x32, 0x45, 0x03]
	HOST_ENABLE_REFRESH_PERIOD = 3;

	def __init__(self, port, stepperDriver, baseline=5):
		threading.Thread.__init__(self);

		self.stepperDriver = stepperDriver;

		self.com = serial.Serial(port=None, baudrate=115200, timeout=1, rtscts=False);
		self.com.port = port;
		self.com.open();

		while(self.com.inWaiting() != 0):
			time.sleep(0.5);
			self.com.reset_input_buffer();

		self.com.write(bytes(EagleDriver.HOST_ENABLE_CMD));
		self.com.flush();
		time.sleep(0.5);

		if(self.com.inWaiting() == 0):
			raise Exception("Device not found. Check EMV");
		print("EMV Connected...");

		self.comLock = Lock();
		self.rotation = None;
		self.baseline = 5;

		self.totalCycles = 0;

		self.isAlive = True;
		self.start();

	def run(self):
		print("Starting EMV");
		while(self.isAlive):
			self.comLock.acquire();
			try:
				self.com.write(bytes(EagleDriver.HOST_ENABLE_CMD));
				self.com.flush();
			finally:
				self.comLock.release();
			
			time.sleep(0.5);
			if(self.com.inWaiting() == 0):
				self.isAlive = False;
				raise Exception("Device Error. Check EMV");
				break;

			time.sleep(max(EagleDriver.HOST_ENABLE_REFRESH_PERIOD-0.5, 0.1));

		print("Stopping EMV");
		return;

	def sendData(self, ID, data):
		if(self.isAlive == False):
			raise Exception("No Device");
			return;

		if(len(bytes([ID])) != 1):
			raise Exception("Invalid ID");

		# data = EagleDriver.asciiEncode(data);
		payload = [ID, 0x33, 0x20] + data + [0x20];

		crc = EagleDriver.calcCRC(payload);
		crc = EagleDriver.asciiEncode(crc, 2);

		payload = [0x02] + payload + crc + [0x03];

		# return(payload);

		self.comLock.acquire();
		try:
			self.com.write(bytes(payload));
			self.com.flush();
			# print(payload);
		finally:
			self.comLock.release();

		return;

	def setPEEP(self, peep):
		peep = min(peep, 30);
		peep = max(peep, 0);

		peep = int((peep+10)*10);
		data = EagleDriver.asciiEncode(peep, 3);

		self.sendData(0x06, data);
		return;

	def sendPulse(self):
		self.stepperDriver.sendPulse();
		return;

	def rotate(self, amplitude, cycles, frequency):
		if(self.rotation != None):
			self.rotation.stop();
		self.rotation = PEEPRotate.PEEPRotate(self, amplitude, self.baseline, cycles, frequency);
		
		self.totalCycles = cycles;
		return;

	def stopRotate(self):
		self.rotation.stop();
		return;

	def getTotalCycles(self):
		return self.totalCycles;

	def setBaseline(self, baseline):
		self.baseline = baseline;
		self.setPEEP(baseline);
		return;

	def stepsRemaining(self):
		if(self.rotation == None):
			return 0;
		return self.rotation.stepsRemaining();


	def shutdown(self):
		self.isAlive = False;
		self.join();
		if(self.com.isOpen()):
			self.com.close();
			del self.com;
		return;

		
	def calcCRC(data):
		crc = 0xFF;
		for d in data:
			crc = EagleDriver.CRC_TABLE[crc ^ d];
		return crc;

	def asciiEncode(data, size):
		if(type(data) == int):
			data = [data];

		tempString = '';
		for d in data:
			tempString = tempString + hex(d).split('x')[1].upper();

		output = []
		for b in tempString:
			output.append(ord(b));

		if(len(output) < size):
			output = [0x30]*(size-len(output)) + output;
		else:
			output = output[-size:];
		return (output);
