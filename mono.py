#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Benjamin Lebsanft"
__copyright__ = "Copyright 2015, Benjamin Grimm-Lebsanft, Monochromator class copyright 2014, Arne Goos"
__license__ = "Public Domain"
__version__ = "1.2.1"
__email__ = "benjamin@lebsanft.org"
__status__ = "Production"

import sys, serial, logging, configparser, time
import datetime as dt
from PyQt4 import QtGui, QtCore

def getWavenumber(self, laserWL, monoWL):
    if(monoWL != "."):
        wavenumber = abs((1/float(laserWL)) - (1/float(monoWL)))*10000000
        return int(round(wavenumber,0))

class Monochromator(object):
    ### Initialises a serial port
    def __init__(self):
        self.mono = serial.Serial(self.comport, timeout=1, baudrate=9600, xonxoff=1, stopbits=1)

        self.config = configparser.RawConfigParser()
        self.config.read('mono.cfg')
        self.comport = self.config.get('Mono_settings', 'com_port')
        self.current_wavelength = self.config.get('Mono_settings', 'current_wavelength')
        self.current_laser_wavelength = self.config.get('Settings', 'laser_wavelength')
        self.speed = self.config.get('Mono_settings', 'speed')
        self.approach_speed = self.config.get('Mono_settings', 'approach_speed')
        self.offset = self.config.get('Mono_settings', 'offset')
        self.nm_per_revolution = self.config.get('Mono_settings', 'nm_per_revolution')
        self.steps_per_revolution = self.config.get('Mono_settings', 'steps_per_revolution')
        self.calibration_offset = self.config.get('Mono_settings', 'calibration_offset')

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
        value = self.mono.readline().decode("utf-8")
        return str(value.rstrip().lstrip())
    
    ### sets the ramp speed
    def setRampspeed(self, rampspeed):
        self.sendcommand('K ' + str(rampspeed))
    
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
        if a[3:].lstrip() == "0":
            return False
        else
            return True
			
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
    if a[3:].lstrip() == "64":
            return "Upper"
        if a[3:].lstrip() == "128":
            return "Lower"
        else:
            return False
        
    def checkHOMEstatus(self):
        self.sendcommand("]")
        value = self.mono.readline().decode("utf-8")
        print("HOME Status complete: " + value)
        print("HOME Status: " + value[3:])
        return str(value[3:].rstrip().lstrip())
		
    def getHomePosition(self): 

        ### This function performs the homing procedure of the monochromator. See
        ### the mono manual for information about the seperate parameters

        ### move to 510 nm before starting the homing procedure

        self.approachWL(510)

        while(self.moving()):
            self.moving()

        ### begin homing procedure

        self.sendcommand("A8")
        self.checkHOMEstatus()
        if(self.checkHOMEstatus() == "32"):
            self.sendcommand("M+23000")
            while(self.checkHOMEstatus() != "2"):
                time.sleep(0.8)
                self.checkHOMEstatus()

            self.sendcommand("@")
            self.sendcommand("-108000")
		
            while(self.moving()):
                self.moving()
				
            self.sendcommand("+72000")

            while(self.moving()):
                self.moving()
				
            self.sendcommand("A24")
	            
            while(self.moving()):
                self.moving()
            
            n1=dt.datetime.now()
			
            self.sendcommand("F1000,0")

            while(self.moving()):
                self.moving()
                n2=dt.datetime.now()
                if (((n2.microsecond-n1.microsecond)/1e6) >= 300):
                    self.sendcommand("@")
                    print("timeout, stopping")
                    break
				
            self.sendcommand("A0")
            self.config.set('Mono_settings', 'current_wavelength', '524.9')
            print("Homing done, setting current wavelength now to 524.9 nm according to mono manual")
            f = open('mono.cfg',"w")
            self.config.write(f)
            Interface.currentMonoWavelengthLabel.setText("524.9 nm")
		
    def approachWL(self, approach_wavelength):		
        Interface.approachButton.setEnabled(False)
        if isinstance(approach_wavelength, float):
            print("Wavelength to approach: " + str(approach_wavelength) + " nm")
            nm_difference = float(approach_wavelength) - float(self.current_wavelength)
            print("Difference in nm: " + str(nm_difference))
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
                time.sleep(time_delay_for_progressbar)
                value = Interface.progressBar.value() + 1
                Interface.progressBar.setValue(value)
                QtGui.qApp.processEvents()
                if (value >= Interface.progressBar.maximum()):
                    Interface.approachButton.setEnabled(True)
                    Interface.progressBar.setValue(0)
                    self.config.set('Mono_settings', 'current_wavelength', approach_wavelength)
                    self.config.set('Settings', 'laser_wavelength', self.current_laser_wavelength)
                    self.current_wavelength = approach_wavelength
                    Interface.currentMonoWavelengthLabel.setText(str(self.current_wavelength) + " nm")
                    f = open('mono.cfg',"w")
                    self.config.write(f)
                    break
        else:
            print("Input is not numeric")
            MessageBox = QtGui.QMessageBox.warning(Interface,"Error:","Input is not numeric") 
            Interface.approachButton.setEnabled(True)
        
class Ui_Form(QtGui.QWidget):
    ### All UI elements go here
    def __init__(self, parent=None):

        ### create main window

        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('InputDialog')

        ### create tabbed interface

        tab_widget = QtGui.QTabWidget()
        tab1 = QtGui.QWidget()
        tab2 = QtGui.QWidget()
        p1_vertical = QtGui.QFormLayout(tab1)
        p2_vertical = QtGui.QFormLayout(tab2)
        tab_widget.addTab(tab1, "Main")
        tab_widget.addTab(tab2, "Advanced") 

        ### create solvent combobox

        self.combo = QtGui.QComboBox(self)
		for key, value in Mono1.config.items('RamanPeaksOfSolvents'):
            self.combo.addItem(key.title())
        self.combo.currentIndexChanged.connect(self.check_combo_state)
        self.combo.currentIndexChanged.emit(self.combo.currentIndex())

        ### create label for current mono wavelength
		
        self.currentMonoWavelengthLabel = QtGui.QLabel(self)
        self.currentMonoWavelengthLabel.setAlignment(QtCore.Qt.AlignRight)
        self.currentMonoWavelengthLabel.setText(Mono1.current_wavelength + " nm")

        ### create input field for wavelength to approach

        self.approachWavelengthInput = QtGui.QLineEdit(self)
        self.approachWavelengthInput.setMaxLength(5)
        self.approachWavelengthInput.setInputMask("999.9")
        self.approachWavelengthInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.approachWavelengthInput.textChanged.connect(self.check_state)
        self.approachWavelengthInput.textChanged.emit(self.approachWavelengthInput.text())

        ### create button to start the mono movement

        self.approachButton = QtGui.QPushButton(self)
        self.approachButton.setObjectName("approachButton")
        self.approachButton.clicked.connect(lambda: Mono1.approachWL(float(self.approachWavelengthInput.text())))
        self.approachButton.setText("Approach")

        ### create input field for current laser wavelength for Raman peak calculations
        
        self.currentLaserWavelengthInput = QtGui.QLineEdit(self)
        self.currentLaserWavelengthInput.setMaxLength(5)
        self.currentLaserWavelengthInput.setInputMask("999.9")
        self.currentLaserWavelengthInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.currentLaserWavelengthInput.setText(Mono1.current_laser_wavelength + " nm")

		### create progress bar for mono movement progress indication
		
        self.progressBar = QtGui.QProgressBar(self)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setMaximum(101)
		
        ### create button for mono homing procedure

        self.homeButton = QtGui.QPushButton(self)
        self.homeButton.setObjectName("homeButton")
        self.homeButton.clicked.connect(lambda: Mono1.getHomePosition())
        self.homeButton.setText("HOME Monochromator")

        ### put widgets into the QFormLayout of tab1

        p1_vertical.addRow("Solvent:", self.combo)
        p1_vertical.addRow("Current Laser Wavelength:", self.currentLaserWavelengthInput)
        p1_vertical.addRow("Current Mono Wavelength:", self.currentMonoWavelengthLabel)
        p1_vertical.addRow("Approach Mono Wavelength:", self.approachWavelengthInput)
        p1_vertical.addRow(self.progressBar, self.approachButton)

        ### put widgets into the QFormLayout of tab2
		
        p2_vertical.addRow("Move to 524.9 nm:", self.homeButton)

        ### set window title and add tab widget to main window

        self.setWindowTitle("Mission control")
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(tab_widget)
        self.setLayout(vbox) 

    def check_combo_state(self, *args, **kwargs):

        ### This function creates an area around the Raman peaks of the solvent
        ### defined in the config file. The range around the peak is defined by
        ### the peak_range setting in the config file.

        global raman_peaks_with_offset

        solvent = self.combo.currentText()
        raman_peaks_list = Mono1.config.get('RamanPeaksOfSolvents', solvent)
        raman_range = Mono1.config.get('Settings', 'peak_range')
        raman_peaks = raman_peaks_list.split(",")
        raman_peaks_with_offset = []
        for i in range(len(raman_peaks)):
            raman_peaks_with_offset += list(range(int(raman_peaks[i])-int(raman_range),int(raman_peaks[i])+int(raman_range)))        
		
    def check_state(self, *args, **kwargs):

        ### This function checks if the wavelength to approach is in the proximity
        ### of Raman peaks of the solvent. If the target wavelength is not in the
        ### peak_range the background of the input field will be green, otherwise
        ### a yellow background informs the user of a possible Raman feature.

        if self.approachWavelengthInput.text() and self.currentLaserWavelengthInput.text():
            wavenumbers = getWavenumber(self.currentLaserWavelengthInput.text(), self.approachWavelengthInput.text())
            print(wavenumbers)
            if wavenumbers in raman_peaks_with_offset:
                color = '#f6f498' # yellow
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
    Interface.setFixedSize(Interface.size());
    app.exec_()
	
