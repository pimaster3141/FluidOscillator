import setuptools
import pyximport; pyximport.install()

import EagleDriver;
import StepperDriver;

class DeviceAPI():


    # devID:    [0-motor
    #            1-25ml Pump
    #            2-2.5ml Pump
    #            3-EMV]
    def __init__(self, motorCOM, emvCOM=None):
        self.motor = StepperDriver.StepperDriver(motorCOM);
        self.emv = None;
        if(emvCOM != None and emvCOM != "None"):
            # print(emvCOM);
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
        if(self.emv != None):
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
    def rotate(self, devID, direction, frequency, amplitude, cycles):
        self.checkID(devID);

        if(devID != 3):
            self.motor.setDevice(StepperDriver.StepperDriver.MOTOR_RESOLUTIONS[devID], devID!=0);
            self.motor.rotate(direction, amplitude, cycles, frequency);
        else:
            self.emv.rotate(amplitude, cycles, frequency);
        return;

    def stop(self, devID):
        self.checkID(devID);

        if(devID != 3):
            self.motor.setDevice(StepperDriver.StepperDriver.MOTOR_RESOLUTIONS[devID], devID!=0);
            self.motor.rotate(0,0,0,0);
        else:
            self.emv.stopRotate();

        return;

    # motor/pump - offset by ml or angle
    # EMV - set PEEP to value;
    def offset(self, devID, direction, offset):
        self.checkID(devID);

        if(devID != 3):
            self.motor.setDevice(StepperDriver.StepperDriver.MOTOR_RESOLUTIONS[devID], devID!=0);
            if(devID == 0):
                self.motor.rotate(direction, 0, offset/360, 0.05);
            else:
                self.motor.rotate(direction, offset, 0, 0.05/offset);
        else:
            self.emv.setBaseline(offset);
        return;

    def isRunning(self, devID):
        self.checkID(devID);

        if(devID != 3):
            return self.motor.isRunning();
        else:
            return (self.emv.stepsRemaining() != 0);

    def percentRemaning(self, devID, steps=100):
        self.checkID(devID);

        if(devID != 3):
            return(steps * self.motor.stepsRemaining()/self.motor.getTotalSteps());
        else:
            if(self.emv.getTotalCycles() == None):
                return steps;
            return(steps * self.emv.stepsRemaining()/self.emv.getTotalCycles());

    def isAnyRunning(self):
        # print("checking things");
        if(self.emv != None):
            return (self.motor.isRunning() or self.emv.isRunning());
        else:
            return(self.motor.isRunning());

    def checkID(self, devID):
        if(devID < 0 or devID > 3):
            raise Exception("Invalid DeviceID");
            
        if(devID == 3 and self.emv == None):
            raise Exception("No EMV Connected!");

