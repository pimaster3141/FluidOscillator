import serial;
import time;

class StepperDriver():
	PACKET_HEADER = 0XAA;
	MOTOR_HEADER = 0XBB;
	PULSE_CMD= 0XCC;
	STATUS_REQ = 0XDD;

	BAUD = 115200;

	def __init__(self, port, resolution):
		self.com = serial.Serial(port=None, baudrate=BAUD, timeout=1, rtscts=False);
		self.com.port = port;
		self.com.open();

		while(self.com.inWaiting() != 0):
			time.sleep(0.5);
			self.com.reset_input_buffer();

		self.sendPacket([STATUS_REQ]);
		self.com.flush();
		time.sleep(1);

		if(self.com.inWaiting() != 7):
			raise Exception("Device not found. Check Motor Controller");
		print("Motor Connected...");
		self.com.read(self.com.inWaiting());

		self.rotationSteps = resolution;
		return;

	def __del__(self):
		self.close();
		return;

	def close(self):
		if(self.com.isOpen()):
			self.com.close();
			del self.com;
		return;

	def sendPacket(self, data):
		self.com.flush();
		self.com.write(bytes([PACKET_HEADER]));
		self.com.flush();
		# print(bytes(data));
		for d in data:
			self.com.write(bytes([d]));
			self.com.flush();
			time.sleep(.05);
		return;

	def sendPulse(self):
		self.sendPacket([PULSE_CMD]);
		return;

	def stepsRemaining(self):
		# time.sleep(0.1);
		self.com.reset_input_buffer()
		self.sendPacket([STATUS_REQ]);

		data = self.com.read(7);
		data = StepperDriver.processBytes(data);
		data[2] = data[2] & 0x3F;

		currRotation = (data[0] << 8) + data[1];
		numQuadrants = data[2];
		reloadValue = (data[5] << 8) + data[6];

		return(currRotation + reloadValue*numQuadrants);

	def isRunning(self):
		# time.sleep(0.1);
		self.com.reset_input_buffer()
		self.sendPacket([STATUS_REQ]);
		
		data = self.com.read(5);
		data = StepperDriver.processBytes(data);
		data[2] = data[2] & 0x3F;
		return(sum(data) != 0);




	def processBytes(data):
		output = []
		for b in data:
			output.append(b);
		return output;
