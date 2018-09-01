import EagleDriver;
import StepperDriver;

class DeviceAPI():


    # devID:    [0-motor
    #            1-25ml Pump
    #            2-2.5ml Pump
    #            3-EMV]
    def __init__(self, motorCOM, devID, emvCOM=None):

        self.motorCOM = motorCOM;
        self.emvCOM = emvCOM;

        return;

    def __delete__(self):
        self.close();
        return;

    # def setDevice(self, motorCOM, devID, emvCOM=None):

    #     self.motorCOM = motorCOM;
    #     self.emvCOM = emvCOM;

    #     return;

    def close(self):
        return;

    def sendPulse(self):
        
        return;

    # Frequency(Hz)
    # Amplitude(ml -or- mmHg) (NOT PEAK-PEAK)
    def rotate(self, devID, direction, frequency, amplitude, rotations):
        self.checkID(devID);

    # motor/pump - offset by ml or angle
    # EMV - set PEEP to value;
    def offset(self, devID, direction, offset):
        self.checkID(devID);

    def isRunning(self, devID):
        self.checkID(devID);
        return True;

    def percentRemaning(self, devID, steps=100):
        self.checkID(devID);
        return steps;

    def isAnyRunning(self):
        return True;

    def checkID(self, devID):
        if(devID < 0 or devID > 3):
            raise Exception("Invalid DeviceID");

        if(devID == 3 and emvCOM == None):
            raise Exception("No EMV COM Specified");
        return;

