import EagleDriver;
import StepperDriver;

class DeviceAPI():

    MOTOR_RESOLUTIONS = [1698, 121, 1212];

    # devID:    [0-motor
    #            1-25ml Pump
    #            2-2.5ml Pump
    #            3-EMV]
    def __init__(self, motorCOM, emvCOM=None):
        self.motor = StepperDriver.StepperDriver(motorCOM);
        self.emv = None;
        if(emvCOM != None):
            self.emv = EagleDriver.EagleDriver(emvCOM, self.motor);

        return;

    def __delete__(self):
        self.close();
        return;

    # def setDevice(self, motorCOM, devID, emvCOM=None):

    #     self.motorCOM = motorCOM;
    #     self.emvCOM = emvCOM;

    #     return;

    def close(self):
        self.emv.shutdown();
        self.motor.close();

        del(self.emv);
        del(self.motor);

        return;

    def sendPulse(self):
        self.motor.sendPulse();
        return;

    # Frequency(Hz)
    # Amplitude(ml -or- mmHg) (NOT PEAK-PEAK)
    def rotate(self, devID, direction, frequency, amplitude, rotations):
        self.checkID(devID);

        if(devID != 3):
            self.motor.setResolution(DeviceAPI.MOTOR_RESOLUTIONS[devID]);
            if(devID == 0):
                self.motor.rotate(direction, frequency)



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
            
        if(devID == 3 and self.emv == None):
            raise Exception("No EMV Connected!");

