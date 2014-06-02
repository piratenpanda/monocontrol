import serial

comport = "COM3"
speed = 20000
approach_speed = 2000

ser = serial.Serial(comport, timeout=1, xonxoff=True)
ser.flushInput()
ser.flushOutput()
ser.writelines(" " +'\r\n')
ser.writelines("V" + str(speed) + '\r\n')
ser.writelines("+67600" + '\r\n')
ser.writelines("W1000" + '\r\n')
ser.writelines("V" + str(approach_speed) + '\r\n')
ser.writelines("-10000" + '\r\n')