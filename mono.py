#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Benjamin Lebsanft"
__copyright__ = "Copyright 2014, Benjamin Lebsanft, Monochromator class copyright 2014, Arne Goos"
__license__ = "Public Domain"
__version__ = "1.1.0"
__email__ = "benjamin@lebsanft.org"
__status__ = "Production"

import sys, serial, logging, configparser, time
from PyQt4 import QtGui, QtCore

class Monochromator(object):
    ### Initialises a serial port
    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.config.read('mono.cfg')
        self.comport = self.config.get('Mono_settings', 'comport')
        self.current_wavelength = self.config.get('Mono_settings', 'current_wavelength')
        self.speed = self.config.get('Mono_settings', 'speed')
        self.approach_speed = self.config.get('Mono_settings', 'approach_speed')
        self.offset = self.config.get('Mono_settings', 'offset')
        self.nm_per_revolution = self.config.get('Mono_settings', 'nm_per_revolution')
        self.steps_per_revolution = self.config.get('Mono_settings', 'steps_per_revolution')
        self.calibration_offset = self.config.get('Mono_settings', 'calibration_offset')
        self.mono = serial.Serial(self.comport, timeout=1)

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
    def setRampspeed(self, rampspeed):
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
		
    def approachWL(self, approach_wavelength):

        if str.isdigit(approach_wavelength):
            print("Wavelength to approach: " + approach_wavelength + " nm")
            nm_difference = float(approach_wavelength) - float(self.current_wavelength) + float(self.calibration_offset)
            print("Difference in nm [calibration offset of " + self.calibration_offset + " nm included]: " + str(nm_difference))
            step_difference = round(((float(nm_difference) / float(self.nm_per_revolution)) * float(self.steps_per_revolution))+ float(self.offset))
            print("Difference in steps: " + str(step_difference))  
            time_needed_sec = abs(step_difference / int(self.speed)) + abs(int(self.offset)/int(self.approach_speed))
            print("Time needed for operation: " + str(time_needed_sec) + " s")
            time_delay_for_progressbar = time_needed_sec / 100
            self.sendcommand("V" + str(self.speed))
            self.sendcommand(str(format(step_difference, '+')))
            self.sendcommand("V" + str(self.approach_speed))
            self.sendcommand("-" + str(self.offset))
            while True:
                Interface.approachButton.setEnabled(False)
                time.sleep(time_delay_for_progressbar)
                value = Interface.progressBar.value() + 1
                Interface.progressBar.setValue(value)
                QtGui.qApp.processEvents()
                if (value >= Interface.progressBar.maximum()):
                    Interface.approachButton.setEnabled(True)
                    Interface.progressBar.setValue(0)
                    self.config.set('Mono_settings', 'current_wavelength', approach_wavelength)
                    self.current_wavelength = int(approach_wavelength)
                    Interface.currentMonoWavelengthLabel.setText(str(self.current_wavelength) + " nm")
                    f = open('mono.cfg',"w")
                    self.config.write(f)
                    break
                   
        else:
            print("Input is not numeric")
            MessageBox = QtGui.QMessageBox.warning(Interface,"Error:","Input is not numeric") 
        
class Ui_Form(QtGui.QWidget):
    ### All UI elements go here
    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('InputDialog')
        self.setFixedSize(300, 150) 

        self.formLayout = QtGui.QFormLayout(self)
        self.currentMonoWavelengthLabel = QtGui.QLabel(self)
        self.currentMonoWavelengthLabel.setAlignment(QtCore.Qt.AlignRight)
		
        self.approachWavelengthInput = QtGui.QLineEdit(self)
        self.approachWavelengthInput.setMaxLength(3)
        self.approachWavelengthInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        
        self.currentLaserWavelengthInput = QtGui.QLineEdit(self)
        self.currentLaserWavelengthInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.combo = QtGui.QComboBox(self)
		
        for key, value in Mono1.config.items('RamanPeaksOfSolvents'):
            self.combo.addItem(key.title())

        self.combo.currentIndexChanged.connect(self.check_combo_state)
        self.combo.currentIndexChanged.emit(self.combo.currentIndex())
		
        self.approachWavelengthInput.textChanged.connect(self.check_state)
        self.approachWavelengthInput.textChanged.emit(self.approachWavelengthInput.text())
		
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setMaximum(101)
		
        self.approachButton = QtGui.QPushButton(self)
        self.approachButton.setObjectName("approachButton")
        self.approachButton.clicked.connect(lambda: Mono1.approachWL(self.approachWavelengthInput.text()))

        self.formLayout.addRow("Solvent:", self.combo)		
        self.formLayout.addRow("Current Laser Wavelength:", self.currentLaserWavelengthInput)
        self.formLayout.addRow("Current Mono Wavelength:", self.currentMonoWavelengthLabel)
        self.formLayout.addRow("Approach Mono Wavelength:", self.approachWavelengthInput)

        self.formLayout.addRow(self.progressBar, self.approachButton)

        self.setWindowTitle("Mission control")     
        self.currentMonoWavelengthLabel.setText(Mono1.current_wavelength + " nm")
        self.approachButton.setText("Approach")
        self.setLayout(self.formLayout)
	
    def getWavenumber(self, laserWL, monoWL):
		
        wavenumber = abs((1/int(laserWL)) - (1/int(monoWL)))*10000000
        return int(round(wavenumber,0))

    def check_combo_state(self, *args, **kwargs):
	
        solvent = self.combo.currentText()
        global raman_peaks_with_offset
        raman_peaks_list = Mono1.config.get('RamanPeaksOfSolvents', solvent)
        raman_range = Mono1.config.get('Settings', 'peak_range')
        raman_peaks = raman_peaks_list.split(",")
        raman_peaks_with_offset = []
        for i in range(len(raman_peaks)):
            raman_peaks_with_offset += list(range(int(raman_peaks[i])-int(raman_range),int(raman_peaks[i])+int(raman_range)))        
		
    def check_state(self, *args, **kwargs):
        if self.approachWavelengthInput.text() and self.currentLaserWavelengthInput.text():
            wavenumbers = self.getWavenumber(self.currentLaserWavelengthInput.text(), self.approachWavelengthInput.text())
            print(wavenumbers)
            if wavenumbers in raman_peaks_with_offset:
                color = '#f6989d' # red
            else:
                color = '#c4df9b' # green
            self.approachWavelengthInput.setStyleSheet('background-color: %s' % color)
		
if __name__ == "__main__":

    Mono1 = Monochromator()
    print("Initializing communication with Monochromator controller...")
    Mono1.sendcommand(' ')        
    app = QtGui.QApplication(sys.argv)
    Interface = Ui_Form()
    Interface.show()
    app.exec_()
	
