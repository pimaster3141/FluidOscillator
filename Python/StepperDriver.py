import serial;
import time;

class StepperDriver():
    PACKET_HEADER = 0XAA;
    MOTOR_HEADER = 0XBB;
    PULSE_CMD= 0XCC;
    STATUS_REQ = 0XDD;

    BAUD = 115200;

    def __init__(self, port, resolution):
        