## 8N1 115200 baud

import serial;
import time;

PACKET_HEADER = 0XAA;
MOTOR_HEADER = 0XBB;
PULSE_CMD= 0XCC;
STATUS_REQ = 0XDD;

BAUD = 115200;
com = None;

ROTATION_STEPS = 1698;
STEP_RATE_INTERVAL = 62500 #Hz
#121 for pump
#1698 for spinny


def initMotor(PORT, RESOLUTION = ROTATION_STEPS):
    global com;
    global ROTATION_STEPS;
    ROTATION_STEPS = RESOLUTION;
    com = serial.Serial(port=None, baudrate = BAUD, timeout = 1, rtscts = False);
    com.port = PORT;
    com.open();
    print(com);

def sendPulse():
    sendPacket([PULSE_CMD]);
    return;

def startMotor(direction = 0, frequency = 0.2, displacement = 1, quadrants = 0):
    #direction unsupported ATM
    payload = [];
    numSteps = round(displacement*ROTATION_STEPS);
    print(str(direction) + "  " + str(frequency)+ "  " +str(displacement)+ "  " +str(quadrants))
    if(frequency == 0):
        duty = 100;
        pulseRate = 0;
    else:
        pulseRate = frequency*ROTATION_STEPS;
        duty = max(45, pulseRate);
        pulseRate = int(STEP_RATE_INTERVAL/pulseRate);

    payload.append(MOTOR_HEADER);
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
    sendPacket(payload);

    rotationIndex = numSteps * (1+quadrants&0x3F);
    return rotationIndex;

def isRunning():
    time.sleep(0.1);
    com.reset_input_buffer()
    sendPacket([STATUS_REQ]);
    
    # time.sleep(0.1);
    data = com.read(5);
    data = processBytes(data);
    data[2] = data[2] & 0x3F;
    return(sum(data) != 0);

def stepsRemaining():
    time.sleep(0.1);
    com.reset_input_buffer()
    sendPacket([STATUS_REQ]);
    
    # time.sleep(0.1);
    data = com.read(7);
    # print(data);
    data = processBytes(data);
    # print(data);
    data[2] = data[2] & 0x3F;

    currRotation = (data[0] << 8) + data[1];
    numQuadrants = data[2];
    reloadValue = (data[5] << 8) + data[6];

    # print(currRotation);
    # print(numQuadrants);
    # print(reloadValue);

    return(currRotation + reloadValue*numQuadrants);


def sendPacket(data):
    com.flush();
    com.write(bytes([PACKET_HEADER]));
    com.flush();
    # print(bytes(data));
    for d in data:
        com.write(bytes([d]));
        com.flush();
        time.sleep(.05);
    return;

def processBytes(data):
    output = []
    for b in data:
        output.append(b);
    return output;

def exitMotor():
    global com
    if(com.isOpen()):
        com.close();
        del com

