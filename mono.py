#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Benjamin Lebsanft"
__copyright__ = "Copyright 2014, Benjamin Lebsanft, Monochromator class Copyright 2014, Arne Goos"
__license__ = "Public Domain"
__version__ = "0.9"
__email__ = "benjamin@lebsanft.org"
__status__ = "Production"

import sys, serial, logging, configparser, time
from PyQt4 import QtGui, QtCore

comport = "COM3"
speed = 20000
approach_speed = 2000
offset = 30000
nm_per_revolution = 12.5 # as we're using a 1200 l/mm grating
steps_per_revolution = 36000

class Monochromator(object):
    ### Initialises a serial port
    def __init__(self):
        self.mono = serial.Serial(comport, timeout=1)
    
    ### sends ascii commands to the serial port and pauses for half a second afterwards
    def sendcommand(self,command):
        self.mono.flushInput()
        self.mono.flushOutput()
        print('Send command: ' + command)
        #logging.debug('Send command: ' + command)
        self.mono.write(bytearray(command + '\r\n','ascii'))
        time.sleep(0.5) 
        
    ### reads ascii text from serial port + formatting
    def readout(self):
        #time.sleep(0.5)
        #self.mono.flushInput()
        a = self.mono.readlines()#[0].lstrip('\r\n')
        if not a == []:
            print('Readout : ' + a[0].rstrip('\r\n'))
            logging.debug('Readout : ' + a[0].rstrip('\r\n'))
            return a[0].rstrip('\r\n')
    
    ### sets the ramp speed
    def setRampspeed(self, Rampspeed):
        self.sendcommand('K ' + str(rampspeed))
        #time.sleep(3)
    
    ### sets the initial velocity    
    def setInitialVelocity(self,initspeed): 
        self.sendcommand('I ' + str(initspeed))
    
    ### sets the velocity   
    def setVelocity(self,velocity):
        self.sendcommand('V ' + str(velocity))
        
    ### checks if the Monochromator is moving (returns True of False) 
    def moving(self):
        self.sendcommand('^')
        a = self.readout()
        if not a[-2] == '0':
            return True
        else:
            return False
        
    def checkfortimeout(self):
        try:
            self.sendcommand('X')
            if self.readout() == None:
                print('Timeout occured')
        except:
            print('Timeout occured')
            
    def checkLimitSwitches(self):
        self.sendcommand("]")
        a = self.readout()
        if a[-2] != '0':
            logging.warning("Limit Switch triggered")
            return True
        else:
            return False
        
    def getHomePosition(): 
        self.sendcommand("A8")
        self.sendcommand("]")
        self.sendcommand("M+23000")
        self.sendcommand("]")
        self.sendcommand("@")
        self.sendcommand("-108000")
        self.sendcommand("+72000")
        self.sendcommand("A24")
        self.sendcommand("F1000,0")
        self.sendcommand("A0")
        
class Ui_Form(QtGui.QWidget):

    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.config = configparser.RawConfigParser()
        self.config.read('mono.cfg')
        self.current_wavelength = self.config.get('Mono_settings', 'current_wavelength')
        self.setWindowTitle('InputDialog')
        self.setFixedSize(250, 100) 

        self.formLayout = QtGui.QFormLayout(self)
        self.currentWavelength = QtGui.QLabel(self)
        self.currentWavelength.setAlignment(QtCore.Qt.AlignRight)
        self.approachButton = QtGui.QPushButton(self)
        self.approachButton.setObjectName("approachButton")
        self.approachButton.clicked.connect(self.approachWL)
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setMaximum(101)
        self.approachWavelength = QtGui.QLineEdit(self)
        self.approachWavelength.setMaxLength(3)
        self.approachWavelength.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.addRow("Current Wavelength:", self.currentWavelength)
        self.formLayout.addRow("Approach Wavelength:", self.approachWavelength)
        self.formLayout.addRow(self.progressBar, self.approachButton)
        self.setWindowTitle("Mission control")     
        self.currentWavelength.setText(self.current_wavelength + " nm")
        self.approachButton.setText("Approach")
        self.setLayout(self.formLayout)
        
    def approachWL(self):
        if str.isdigit(self.approachWavelength.text()):
            print("Wavelength to approach: " + self.approachWavelength.text() + " nm")
            nm_difference = int(self.approachWavelength.text()) - int(self.current_wavelength)
            print("Difference in nm: " + str(nm_difference))
            step_difference = round(((nm_difference / nm_per_revolution) * steps_per_revolution)+ offset)
            print("Difference in steps: " + str(step_difference))  
            time_needed_sec = abs(step_difference / speed) + abs(offset/approach_speed)
            print("Time needed for operation: " + str(time_needed_sec) + " s")
            time_delay_for_progressbar = time_needed_sec / 100
            Mono1.sendcommand("V" + str(speed))
            Mono1.sendcommand(str(format(step_difference, '+')))
            Mono1.sendcommand("V" + str(approach_speed))
            Mono1.sendcommand("-" + str(offset))
            while True:
                self.approachButton.setEnabled(False)
                time.sleep(time_delay_for_progressbar)
                value = self.progressBar.value() + 1
                self.progressBar.setValue(value)
                QtGui.qApp.processEvents()
                if (value >= self.progressBar.maximum()):
                    self.approachButton.setEnabled(True)
                    self.progressBar.setValue(0)
                    self.config.set('Mono_settings', 'current_wavelength', self.approachWavelength.text())
                    self.current_wavelength = int(self.approachWavelength.text())
                    self.currentWavelength.setText(str(self.current_wavelength) + " nm")
                    f = open('mono.cfg',"w")
                    self.config.write(f)
                    break
                   
        else:
            print("Input is not numeric")
            self.MessageBox = QtGui.QMessageBox.warning(self,
                            "Error:",
                            "Input is not numeric") 
	
if __name__ == "__main__":

    Mono1 = Monochromator()
    print("Initializing communication with Monochromator controller...")
    Mono1.sendcommand(' ')
        
    app = QtGui.QApplication(sys.argv)
    icon = Ui_Form()
    icon.show()
    app.exec_()

