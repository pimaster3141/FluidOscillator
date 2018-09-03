# -*- coding: utf-8 -*-


from tkinter import *
from tkinter import messagebox as mb
from tkinter import filedialog, simpledialog
from tkinter import ttk
import time
import csv
import DeviceAPI
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
        self.tick = 500 #refresh rate in ms
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
        self.motorCOM = StringVar()
        self.emvCOM = StringVar()
        self.MotorNames = ["Motor", "Pump 25ml", "Pump 2.5ml"]
        self.MotorSelection = StringVar() 
        self.MotorSelection.set(self.MotorNames[-1])
        self.motorCOM.set(self.portNames[-1])
        self.emvCOM.set("None")
        self.totalDuration = 0
        self.lastTime = time.time()
        self.ml = 0.0
        self.alarmsound = "beep.wav"
        self.commandTime = 0
        self.isalarming = 1

        self.device = [] # deviceAPI object
        self.devID = 0
        
        #start window
        master.title("Fluid Oscillator")
        master.minsize(width=200, height=100)
        
        # *** MENU ***
        self.menu = Menu(master)
        master.config(menu=self.menu)
        # ----------------------------------------------------------------------
        self.subMenu = Menu(self.menu)
        self.menu.add_cascade(label="File",menu=self.subMenu)
        self.subMenu.add_command(label="New Project...",command=self.loadProject)
        self.subMenu.add_separator()
        self.subMenu.add_command(label="Exit",command=self.quit)
        # ----------------------------------------------------------------------
        self.editMenu = Menu(self.menu)
        self.menu.add_cascade(label="Edit",menu=self.editMenu)
        # ----------------------------------------------------------------------
        
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
        self.deviceMenu = OptionMenu(self.toolbar, self.MotorSelection, *self.MotorNames, command=self.changeDevice)
        self.deviceMenu.pack(side=LEFT, padx=2, pady=2)
        self.deviceMenu.configure(state="disabled")
        self.OffsetButt = Button(self.toolbar, text="Offset...", command=self.offsetWin, state='disabled')
        self.OffsetButt.pack(side=RIGHT, padx=2, pady=2)
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
            self.commandTime = self.device.rotate(0,0,0,0)
            self.device.close()
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
            with open(self.filename) as csvfile:
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
        self.device.sendPulse();
        
    def isRotating(self):
        self.motorState = self.device.isRunning();
        return self.motorState
    
    def remainingSteps(self):
        if self.commandTime != 0:
            remain = self.device.stepsRemaining()
            self.remainingTime = self.commandTime - remain
            self.pb["value"]=(1.0*self.remainingTime/self.commandTime)*100
            print(self.isalarming)
            if (1.0*self.remainingTime/self.commandTime)*100 > 90.0 and self.schedule[self.n-1] == TRUE and self.isalarming == 0:
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
                        self.commandTime = self.device.rotate(self.dir[self.n], self.frq[self.n], self.vol[self.n], self.T[self.n])
                        self.motorState=TRUE
                        self.status['text'] = 'Rotating at ' + str(self.frq[self.n]) + 'Hz...'
                        self.n += 1
            self.remainingSteps()
        self.master.after(self.tick,self.runExperiment)
                
        
    def setPort(self):
        try:
            self.device.close()
        except:
            pass
        self.portNames = serial_ports()
        self.motorCOM.set(self.portNames[-1])
        self.popup = Toplevel()
        self.popup.title("Select ports")
        self.deviceMenu.configure(state="disabled")
        Label(self.popup, text = "Motor Driver: ", justify=LEFT, anchor="e",width=15).grid(row=0,column=0)
        OptionMenu(self.popup, self.motorCOM,*self.portNames).grid(row=0,column=1)
        Label(self.popup, text = "Ventilator EMV: ", justify=LEFT, anchor="e",width=15).grid(row=1,column=0)
        OptionMenu(self.popup, self.emvCOM,*self.portNames).grid(row=1,column=1)
        Button(self.popup, text = "Connect", command = self.connectPort).grid(row=2, column=0, columnspan=2)
        self.popup.mainloop()
        
    def connectPort(self):
        print(self.emvCOM.get())
        print(self.motorCOM.get())
        self.device = DeviceAPI(self.motorCOM.get(),self.devID,self.emvCOM.get())
        self.deviceMenu.configure(state="normal")
        self.startButt['state'] = 'normal'
        self.stopButt['state']  = 'disabled'
        self.markButt['state']  = 'normal'
        self.OffsetButt['state']  = 'normal'
        self.deviceMenu['state'] = 'normal'
        self.status['text'] = 'Motor Controller via: ' + self.motorCOM.get() + 'EMV+ via: ' + self.emvCOM.get()
        self.popup.destroy()
        del self.popup

    def changeDevice(self,deviceName):
        if not self.isRotating():
            self.devID = self.portNames.index(self.MotorSelection.get())
            self.device.setDevice(self.devID)

    def offsetWin(self):
        self.popup = Toplevel()
        self.popup.title("Offset Device Position")
        if self.devID == 0: # Motor
            self.ml = simpledialog.askfloat("Amount", "Degree offset [deg], +:CCW", parent=self.popup, minvalue=-360.0, maxvalue=360, initialvalue=self.ml)
        elif self.devID == 3: # EMV+
            self.ml = simpledialog.askfloat("Amount", "PEEP offset [mmHg]", parent=self.popup, minvalue=-30.0, maxvalue=30, initialvalue=self.ml)
        else: 
            if self.devID == 1:
                den=1.0
            else:
                den = 10.0
            self.ml = simpledialog.askfloat("Amount", "Enter volume [ml], +:fill", parent=self.popup, minvalue=-25/den, maxvalue=25/den, initialvalue=self.ml)
        self.Button(self.popup, text = "GO", command = self.offset)
        self.popup.mainloop()

    def offset(self):
        if self.isRotating() == FALSE:
            if self.ml is not None:
                self.status['text'] = 'Filling...'
                self.status.update()
                self.commandTime = self.device.offset(self.ml)
                time.sleep((int(self.ml / (0.5/den) + 0.1)))

    def start(self):
        if len(self.schedule) == 0:
            mb.showwarning("Abort.","No project found.")
        else:
            self.hasStarted = TRUE
            self.device.rotate(0,0,0,0)
            self.n = 0;
            self.isalarming = 0
            self.timeleft = self.totalDuration
            self.lastTime = time.time();
            self.deviceMenu.configure(state="disabled")
            self.startButt['state'] = 'disabled'
            self.stopButt['state'] = 'normal'
            self.status['text'] = 'Start...'
            self.OffsetButt['state'] = 'disabled'
            self.deviceMenu['state'] = 'disabled'
        
    def stop(self):
        if self.hasStarted:
            self.hasStarted = FALSE
            self.device.rotate(0,0,0,0)
            self.stopButt['state'] = 'disabled'
            self.startButt['state'] = 'normal'
            self.status['text'] = 'Done.'
            self.OffsetButt['state'] = 'normal'
            self.deviceMenu['state'] = 'normal'
            self.deviceMenu.configure(state="normal")
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
        for n in range(self.N):
            if self.schedule[n] == TRUE:
                self.totalDuration += ((1.0 / self.frq[n]) * self.T[n])
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
            self.commandTime = self.device.rotate(0,0,0,0)
#            self.n = 0;
            self.stopButt['state'] = 'disabled'
            self.startButt['state'] = 'normal'
            self.status['text'] = 'Done.'
            self.OffsetButt['state'] = 'normal'
            self.deviceMenu['state'] = 'normal'
            self.Timer['text'] = "00:00:00"
            self.timeleft = self.totalDuration
            
                             
        
    def kill(self):
        self.commandTime = self.device.rotate(0,0,0,0)
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

    result = ['None']
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
