# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from tkinter import *
from tkinter import messagebox as mb
from tkinter import filedialog, simpledialog
from tkinter import ttk
import time
import csv
from StepperDriver import *
import os
import sys
import glob
import serial
import code
from datetime import timedelta
import winsound

class Oscillator():
    def __init__(self, master):
        # variables
        self.master = master
        self.tick = 500
        self.motorState = FALSE
        self.hasStarted = FALSE
        self.n = 0 # current frequency
        self.N = 0 # max frequencies
        self.frq = [] # list of frequencies 
        self.T   = [] # list of # of rotations / frq 
        self.vol = [] # stroke volume
        self.dir = [] # list of directions
        self.schedule = [] # 1 = rotating 0: pause
        self.pause = [] # pause duration
        self.filename =''
        self.startPausing = bool(1)
        self.startTime = 0.0
        self.portNames = serial_ports()
        self.rotationSteps = IntVar()
        self.rotationSteps.set(1212)
        self.port = StringVar()
        self.MotorNames = ['Motor', 'Pump 25ml', 'Pump 2.5ml']
        self.MotorSelection = StringVar() 
        self.MotorSelection.set(self.MotorNames[-1])
        self.port.set(self.portNames[-1])
        self.totalDuration = 0
        self.lastTime = time.time()
        self.ml = 0.1
        self.alarmsound = "beep.wav"
        self.commandTime = 0
        self.isalarming = 1
        #start window
        master.title("Fluid Oscillator")
        master.minsize(width=200, height=100)
        
        # *** MENU ***
        self.menu = Menu(master)
        master.config(menu=self.menu)
        # -------------------------------------------------------------------
        self.subMenu = Menu(self.menu)
        self.menu.add_cascade(label="File",menu=self.subMenu)
        self.subMenu.add_command(label="New Project...",command=self.loadProject)
        self.subMenu.add_separator()
        self.subMenu.add_command(label="Exit",command=self.quit)
        # -------------------------------------------------------------------
        self.editMenu = Menu(self.menu)
        self.menu.add_cascade(label="Edit",menu=self.editMenu)
        
        # -------------------------------------------------------------------    
        
        # *** Toolbar ***
        self.toolbar = Frame(master, bg="grey")
        self.startButt = Button(self.toolbar, text="Start", command=self.start, state='disabled')
        self.startButt.pack(side=LEFT, padx=2, pady=2)
        self.stopButt =  Button(self.toolbar, text="Stop", command=self.stop, state='disabled')
        self.stopButt.pack(side=LEFT, padx=2, pady=2)
        self.markButt =  Button(self.toolbar, text="Mark", command=self.setMarker, state='disabled')
        self.markButt.pack(side=LEFT, padx=2, pady=2)
        self.portButt =  Button(self.toolbar, text="Port...", command=self.setPort)
        self.portButt.pack(side=LEFT, padx=2, pady=2)
        self.FillButt =  Button(self.toolbar, text="Fill", command=self.fill, state='disabled')
        self.FillButt.pack(side=RIGHT, padx=2, pady=2)
        self.EjectButt =  Button(self.toolbar, text="Eject", command=self.eject, state='disabled')
        self.EjectButt.pack(side=RIGHT, padx=2, pady=2)
        self.Timer = Label(self.toolbar, text="00:00:00")
        self.Timer.pack(side=RIGHT, padx=4, pady=2)
        
        self.toolbar.pack(side=TOP, fill=X)
        
        # *** Progressbar ***
        self.pbFrame = Frame()
        self.pbFrame.pack(expand=True, fill=BOTH, side=TOP)
        self.pb = ttk.Progressbar(self.pbFrame, orient='horizontal', mode='determinate')
        self.pb.pack(expand=True, fill=BOTH, side=TOP)
        
        # *** Schedule *** 
        self.table = Frame(master)
        self.showSchedule()
        
        
        # *** Status Bar ***
        self.status = Label(master, text="Preparing to do nothing...", bd=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=BOTTOM, fill=X)
        master.after(self.tick,self.runExperiment)
        
    def __del__(self):
        try:
            self.commandTime = startMotor(0,0,0,0)
            exitMotor()
        except Exception as e:
            print(e)
            print("Did not exit motor.")

    def quit(self):
        self.master.destroy()
    
    def loadProject(self):
        self.cleanup()
        self.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))
        # print(self.filename)
        if self.filename != '':
            with open(app.filename) as csvfile:
                reader = csv.DictReader(csvfile)
                line = 0
                self.N = 0
                for row in reader:
                    line += 1
                    schedule = row['#']
                    duration = row['duration']
                    freq = row['freq']
                    direction = row['direction']
                    vol = row['volume']
                    if schedule == "PAUSE":
                        self.schedule.append(bool(0))
                        self.pause.append(float(duration))
                        self.T.append(float(0))
                        self.dir.append(bool(0))
                        self.frq.append(float(0))
                        self.vol.append(float(0))
                        self.N+=1
                    elif schedule == "RUN":
                        self.schedule.append(bool(1))
                        self.pause.append(0)
                        self.T.append(float(duration))
                        if direction == "CW" or direction == "cw":
                            self.dir.append(bool(1))
                        elif direction == "CCW" or direction == "ccw":
                            self.dir.append(bool(0))
                        else:
                            self.cleanup()
                            mb.showerror("False Statement","Rotation direction in line "+ str(line) + " unknown.")
                        self.frq.append(float(freq))
                        self.vol.append(float(vol))
                        self.N+=1
                    elif schedule == "#":
                        continue
                        # ignore comment
                    else:
                        mb.showerror("False Statement","Command in line "+ str(line) + " unknown.")
            
            self.showSchedule()
            self.calcDuration()
        
    def showSchedule(self):
        b = Label(self.table, text="", justify=RIGHT, anchor="e",width=10)
        b.grid(row=0, column=1)
        b = Label(self.table, text="Duration",justify=LEFT,width=20)
        b.grid(row=0, column=2)
        b = Label(self.table, text="Frequency",justify=LEFT,width=20)
        b.grid(row=0, column=3)
        b = Label(self.table, text="Direction",justify=LEFT,width=20)
        b.grid(row=0, column=4)
        b = Label(self.table, text="Volume",justify=LEFT,width=20)
        b.grid(row=0, column=5)
        for i in range(self.N): #Rows
            if self.schedule[i]==1:
                b = Label(self.table, text="ROTATION", justify=RIGHT, anchor="e", fg="green")
                b.grid(row=i+1, column=1)
                b = Label(self.table, text=str(self.T[i]),justify=LEFT)
                b.grid(row=i+1, column=2)
                b = Label(self.table, text=str(self.frq[i]),justify=LEFT)
                b.grid(row=i+1, column=3)
                b = Label(self.table, text=str(self.dir[i]),justify=LEFT)
                b.grid(row=i+1, column=4)
                b = Label(self.table, text=str(self.vol[i]),justify=LEFT)
                b.grid(row=i+1, column=5)
                
            else:
                b = Label(self.table, text="PAUSE", justify=RIGHT, anchor="e")
                b.grid(row=i+1, column=1)
                b = Label(self.table, text=str(self.pause[i]),justify=LEFT)
                b.grid(row=i+1, column=2)
                b = Label(self.table, text="",justify=LEFT)
                b.grid(row=i+1, column=3)
                b = Label(self.table, text="",justify=LEFT)
                b.grid(row=i+1, column=4)
                b = Label(self.table, text="",justify=LEFT)
                b.grid(row=i+1, column=5)
        self.table.pack(side=TOP,fill=X)    
            
    def setMarker(self):
        sendPulse();
        
    def isRotating(self):
#        try:
        self.motorState = isRunning();
#        except:
#            print('EXCEPT')
#            self.motorState = FALSE
        return self.motorState
    
    def remainingSteps(self):
        if self.commandTime != 0:
            remain = stepsRemaining()
            self.remainingTime = self.commandTime - remain
            self.pb["value"]=(1.0*self.remainingTime/self.commandTime)*100
            print(self.isalarming)
            if (1.0*self.remainingTime/self.commandTime)*100 > 90.0 and self.schedule[self.n-1] == TRUE and self.isalarming == 0:
                print("CHUPCHUP")
                self.isalarming = 1
                try:
                    winsound.PlaySound(self.alarmsound, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP)
                except:
                    pass
        else:
            self.pb["value"]=0
    
    def runExperiment(self):
        if self.hasStarted: 
            self.clock()
            if self.n < self.N:
                if not self.isRotating():
                    if self.schedule[self.n] == FALSE: # false == pause
                        if self.startPausing:
                            self.startTime = time.time()
                            self.startPausing = bool(0)
                            self.status['text'] = 'Pausing...'
                            
                        if time.time() - self.startTime >= self.pause[self.n]:
                            self.n += 1
                            self.startPausing = bool(1)
                            self.status['text'] = 'Pausing...'
                            
                    else: # true == spin command
                        self.isalarming = 0
                        if self.rotationSteps.get() == 121 or self.rotationSteps.get() == 1212:
                            self.commandTime = startMotor(self.dir[self.n], (self.vol[self.n] * self.frq[self.n] * 4.), self.vol[self.n],int(self.T[self.n]*4-1))
                        else:
                            self.commandTime = startMotor(self.dir[self.n], self.frq[self.n], self.T[self.n],0)
                        self.motorState=TRUE
                        self.status['text'] = 'Rotating at ' + str(self.frq[self.n]) + 'Hz...'
                        self.n += 1
            self.remainingSteps()
        self.master.after(self.tick,self.runExperiment)
                
        
    def setPort(self):
        try:
            exitMotor()
        except:
            pass
        self.portNames = serial_ports()
        self.port.set(self.portNames[-1])
        self.popup = Toplevel()
        self.popup.title("Select a port")
        w = OptionMenu(self.popup, self.port,*self.portNames)
        w.pack()
        w = OptionMenu(self.popup, self.MotorSelection, *self.MotorNames)
        w.pack()
        
        button = Button(self.popup, text = "OK", command = self.connectPort)
        button.pack()
        self.popup.mainloop()
        
    def connectPort(self):
        self.getStepCount()
        initMotor(self.port.get(),int(self.rotationSteps.get()))
        self.startButt['state'] = 'normal'
        self.stopButt['state']  = 'disabled'
        self.markButt['state']  = 'normal'
        self.FillButt['state']  = 'normal'
        self.EjectButt['state'] = 'normal'
        self.status['text'] = 'connected to ' + self.port.get()
        self.popup.destroy()
        del self.popup
        
        
    def start(self):
        if len(self.schedule) == 0:
            mb.showwarning("Abort.","No project found.")
        else:
            self.hasStarted = TRUE
            self.commandTime = startMotor(0,0,0,0)
            self.n = 0;
            self.isalarming = 0
            self.timeleft = self.totalDuration
            self.lastTime = time.time();
            self.startButt['state'] = 'disabled'
            self.stopButt['state'] = 'normal'
            self.status['text'] = 'Start...'
            self.FillButt['state'] = 'disabled'
            self.EjectButt['state'] = 'disabled'
        
    def stop(self):
        if self.hasStarted:
            self.hasStarted = FALSE
            self.commandTime = startMotor(0,0,0,0)
            self.stopButt['state'] = 'disabled'
            self.startButt['state'] = 'normal'
            self.status['text'] = 'Done.'
            self.FillButt['state'] = 'normal'
            self.EjectButt['state'] = 'normal'
            self.isalarming = 1
       
    def cleanup(self):
        for widget in self.table.winfo_children():
            widget.destroy()
        self.n = 0 # current frequency
        self.N = 0 # max frequencies
        self.frq = [] # list of frequencies 
        self.T   = [] # list of # of rotations / frq 
        self.vol = []
        self.dir = [] # list of directions
        self.schedule = [] # 1 = rotating 0: pause
        self.pause = [] # pause duration
        self.filename =''
        self.startPausing = bool(1)
        self.startTime = 0.0
        self.totalDuration = 0
        self.calcDuration()
        self.status['text'] = 'Ready'
        self.hasStarted = FALSE
        self.isalarming = 1
        
    def calcDuration(self):
        self.totalDuration = 0
        if self.rotationSteps.get() == 121 or self.rotationSteps.get() == 1212:
            for n in range(self.N):
                if self.schedule[n] == TRUE:
                    self.totalDuration += ((1.0 / self.frq[n]) * self.T[n])
                else:
                    self.totalDuration += self.pause[n]
        else:
            for n in range(self.N):
                if self.schedule[n] == TRUE:
                    self.totalDuration += (self.T[n] /self.frq[n])
                else:
                    self.totalDuration += self.pause[n]
        self.totalDuration += self.N*2;
        self.Timer['text'] = timedelta(seconds=int(self.totalDuration))
        self.status['text'] = 'Ready'
        
    def clock(self):
        self.timeleft -= time.time() - self.lastTime
        self.lastTime = time.time()
        if self.timeleft >=0:
            self.Timer['text'] = timedelta(seconds=int(self.timeleft))
        else:
            self.hasStarted = FALSE
            self.commandTime = startMotor(0,0,0,0)
#            self.n = 0;
            self.stopButt['state'] = 'disabled'
            self.startButt['state'] = 'normal'
            self.status['text'] = 'Done.'
            self.FillButt['state'] = 'normal'
            self.EjectButt['state'] = 'normal'
            self.Timer['text'] = "00:00:00"
            self.timeleft = self.totalDuration
                            
            
    def fill(self):
        if self.isRotating() == FALSE:
            if self.rotationSteps.get() == 121 or self.rotationSteps.get() == 1212:
                if self.rotationSteps.get() == 121:
                    den=1.0
                else:
                    den = 10.0
                self.ml = simpledialog.askfloat("Fill", "Enter volume [ml]", parent=self.master, minvalue=0.0, maxvalue=25/den, initialvalue=self.ml)
                if self.ml is not None:
                    self.status['text'] = 'Filling...'
                    self.status.update()
                    self.commandTime = startMotor(0, 0.5/den, self.ml,0)
                    time.sleep((int(self.ml / (0.5/den) + 0.1)))
                    self.kill()
            else:
                messagebox.showinfo('Info','Only valid with pump.')
        
    def eject(self):
        if self.isRotating() == FALSE:
            if self.rotationSteps.get() == 121 or self.rotationSteps.get() == 1212:
                if self.rotationSteps.get() == 121:
                    den=1.0
                else:
                    den = 10.0
                self.ml = simpledialog.askfloat("Eject", "Enter volume [ml]", parent=self.master, minvalue=0.0, maxvalue=25/den, initialvalue=self.ml)
                if self.ml is not None:
                    self.status['text'] = 'Ejecting...'
                    self.status.update()
                    self.commandTime = startMotor(1, 0.5/den, self.ml,0)
                    time.sleep((int((self.ml / (0.5/den)) + 0.1)))
                    self.kill()
                
            else:
                messagebox.showinfo('Info','Only valid with pump.')
                             
    def getStepCount(self):
        if self.MotorSelection.get() == 'Motor':
            self.rotationSteps.set(1698)
        elif self.MotorSelection.get() == 'Pump 25ml':
            self.rotationSteps.set(121)
        elif self.MotorSelection.get() == 'Pump 2.5ml':
            self.rotationSteps.set(1212)
        else:
            return
        
    def kill(self):
        self.commandTime = startMotor(0,0,0,0)
        self.status['text'] = 'Done.'
        
##########################################################################
# -------------------------- HELPER FUNC --------------------------------#
##########################################################################


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


##########################################################################
# -------------------------- RUN PROGRAM --------------------------------#
##########################################################################

root = Tk()  
app = Oscillator(root)
root.mainloop()
del app

# code.interact(local=locals())