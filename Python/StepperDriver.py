import serial;
import time;

class StepperDriver():
	PACKET_HEADER = 0XAA;
	MOTOR_HEADER = 0XBB;
	PULSE_CMD= 0XCC;
	STATUS_REQ = 0XDD;

	BAUD = 115200;

	STEP_RATE_INTERVAL = 62500;

	MOTOR_RESOLUTIONS = [1698, 121, 1212];

	def __init__(self, port, resolution=None, pump=True):
		self.com = serial.Serial(port=None, baudrate=StepperDriver.BAUD, timeout=1, rtscts=False);
		self.com.port = port;
		self.com.open();

		while(self.com.inWaiting() != 0):
			time.sleep(0.5);
			self.com.reset_input_buffer();

		self.sendPacket([StepperDriver.STATUS_REQ]);
		self.com.flush();
		time.sleep(1);

		if(self.com.inWaiting() != 7):
			print(self.com.inWaiting());
			raise Exception("Device not found. Check Motor Controller");
		print("Motor Connected...");
		self.com.read(self.com.inWaiting());

		self.rotationSteps = resolution;
		self.pump = pump;

		self.totalSteps = 0;
		return;

	def __del__(self):
		self.close();
		return;

	def setDevice(self, resolution, pump):
		self.rotationSteps = resolution;
		self.pump = pump;
		return;

	def close(self):
		if(self.com.isOpen()):
			self.com.close();
			del self.com;
		return;

	def sendPacket(self, data):
		self.com.flush();
		self.com.write(bytes([StepperDriver.PACKET_HEADER]));
		self.com.flush();
		# print(bytes(data));
		for d in data:
			self.com.write(bytes([d]));
			self.com.flush();
			time.sleep(.05);
		return;

	def sendPulse(self):
		self.sendPacket([StepperDriver.PULSE_CMD]);
		return;

	def rotate(self, direction, amplitude, cycles, frequency):
	# def rotate(self, direction=0, frequency=0.2, displacement=1, quadrants=0):
		if(self.pump):
			frequency = amplitude * frequency * 4;
			displacement = amplitude;
			quadrants = round(cycles *4-1);
			if(quadrants < 0):
				quadrants = 0;
		else:
			displacement = cycles;
			quadrants = 0;


		#direction unsupported ATM
		payload = [];
		numSteps = round(displacement*self.rotationSteps);
		# print(str(direction) + "  " + str(frequency)+ "  " +str(displacement)+ "  " +str(quadrants))
		if(frequency == 0):
			duty = 100;
			pulseRate = 0;
		else:
			pulseRate = frequency*self.rotationSteps;
			duty = max(45, pulseRate);
			pulseRate = int(StepperDriver.STEP_RATE_INTERVAL/pulseRate);

		payload.append(StepperDriver.MOTOR_HEADER);
		payload.append(int(min(duty, 100))) # duty 

		# if(pulseRate<256):
		#   payload.append(0);
		# payload.append(pulseRate);
		payload.append((pulseRate >> 8) & 0x00FF);
		payload.append(pulseRate & 0x00FF);

		# if(numSteps<256):
		#   payload.append(0);
		# payload.append(numSteps);
		payload.append((numSteps >> 8) & 0x00FF);
		payload.append(numSteps & 0x00FF);

		if(direction):
			payload.append(0x40 + (quadrants & 0x3F));
		else:
			payload.append(0xC0 + (quadrants & 0x3F));

		# print(payload);
		self.sendPacket(payload);

		self.totalSteps = numSteps * (1+quadrants&0x3F);
		# return rotationIndex;

	def stepsRemaining(self):
		# time.sleep(0.1);
		self.com.reset_input_buffer()
		self.sendPacket([StepperDriver.STATUS_REQ]);

		data = self.com.read(7);
		data = StepperDriver.processBytes(data);
		data[2] = data[2] & 0x3F;

		currRotation = (data[0] << 8) + data[1];
		numQuadrants = data[2];
		reloadValue = (data[5] << 8) + data[6];

		return(currRotation + reloadValue*numQuadrants);

	def getTotalSteps(self):
		return self.totalSteps;

	def isRunning(self):
		# time.sleep(0.1);
		self.com.reset_input_buffer()
		self.sendPacket([StepperDriver.STATUS_REQ]);
		
		data = self.com.read(5);
		data = StepperDriver.processBytes(data);
		data[2] = data[2] & 0x3F;
		return(sum(data) != 0);

	def processBytes(data):
		output = []
		for b in data:
			output.append(b);
		return output;
