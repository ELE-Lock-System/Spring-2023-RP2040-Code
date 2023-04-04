"""
If you have the breadboard prototype ignore the Pico
that is not connected to the scanner, that is the
Picoprobe which is mainly used for C debugging
    - If you want to flash to it go ahead, I have
    the Picoprobe tool on my laptop and can reflash it
    
How to program from Thonny to Pico-Lock

1. Bottom right of Thonny there is the current interpeter
    click on it and select "Configure Interpeter"
    a. If this is the first time firing up Thonny and connecting the Pico
        then you need to select Micropython onto the Pico
        i. After this Micropython (Raspberry Pi Pico)
    b. For the kind of interpeter, select "Micropython (Raspberry Pi Pico)"
2. After selecting the interpeter start coding
3. Save the code onto the Pico
    a. Alternatively we can run the code by pressing the green button
    
"""
from machine import Pin, UART, PWM, I2C
import time
import utime

#---- Functions ----#
"""
 Do attempt to scan or trigger scanner while sending commands.
 The scanner will buffer in an attempted scan while a
 command is being sent and a b'' value will show up and the
 ACK byte will buffer in afterwards
 During set up point scanner towards a wall or something
 that wont move
"""
def inputTx0(txData):
    uart0.write(txData)
    time.sleep(1)
    
    
def outputRx():
    # Note that only commands return 0x06 or 0x15
    # Sometimes the commands return a byte of b'',
    # this means the scanner will append a byte of 0x06
    # in the scan buffer, scanner logic handles it
    # sometimes if the scanner is sending data and then interrupted, then
    # commands will return 0,
    data = bytes()
    #print(uart0.any())
    while uart0.any() > 0:
        led.value(1)
        data += uart0.read(1)
        time.sleep(1)
        led.value(0)
        
    if data == b'\x06':
        return "Success"
    
    if data == b'\x15':
        return "Error"
        
    if data != b'\x15' and data != b'\x06':
        return data

def resetScanner():
    temp = ""
    cmd = bytes()
    cmd = b'^_^DEFALT.'
    print("RESET")
    inputTx0(cmd)
    temp = outputRx()
    print(temp)

def ttlMode():
    temp = ""
    cmd = bytes()
    cmd = b'^_^POR232.'
    print("TTL/RS232 Mode!")
    inputTx0(cmd)
    temp = outputRx()
    print(temp)

def motionOn():
    temp = ""
    cmd = bytes()
    cmd = b'^_^SCMMDH.'
    print("Enabling Motion Sense!")
    inputTx0(cmd)
    temp = outputRx()
    print(temp)
    
def lightsOff():
    temp = ""
    cmd = bytes()
    cmd = b'^_^LAMENA0.'
    print("Turning off aux lights")
    inputTx0(cmd)
    temp = outputRx()
    print(temp)
    
    
    
def qrModeOn():
    temp = ""
    cmd = bytes()
    cmd = b'^_^QRCENA1.'
    print("Enabling QR Code Readability")
    inputTx0(cmd)
    temp = outputRx()
    print(temp)
    
def motionSense(sense):
    temp = ""
    cmd = bytes()
    if sense == 20:
        inputTx0(b'^_^MDTTHR20.')
        print("Enabling HIGH Sensitivity")
        outputRx()
        return
    
    if sense == 50:
        cmd = b'^_^MDTTHR50.'
        inputTx0(cmd)
        print("Enabling MEDIUM Sensitivity")
        temp = outputRx();
        print(temp)
        return
        
    if sense == 100:
        inputTx0(b'^_^MDTTHR100.')
        print("Enabling LOW Sensitivity")
        outputRx()
        return
    
    print("No change in sensitivity")
    
def servo_lock(angle_target):
    # Calculate duty cycle value for duty target
    duty_target = int((angle_target - angle_min) / angle_range * duty_range + duty_min)

    # Rotate servo to 90 degrees
    pwm.duty_u16(duty_target)
    # Wait for servo to rotate to target angle
    utime.sleep(1)

    # Clean up
    pwm.deinit()
        
    
#---- main ----#
# Set up UART for the scanner
uart0 = UART(0, baudrate=115200, tx=Pin(12), rx=Pin(13))
# Set up UART for the Pi 4
uart1 = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
# Set up PWM pin for servo
pwm_pin = Pin(17)
pwm = PWM(pwm_pin)
pwm.freq(50)
# Set up servo motor angle control variables
angle_min = 0      # Minimum angle of servo
angle_max = 270    # Maximum angle of servo
duty_min = 2000    # Duty cycle value for minimum angle
duty_max = 7500    # Duty cycle value for maximum angle
angle_range = angle_max - angle_min
duty_range = duty_max - duty_min

# Set up status LED
led = Pin(25, Pin.OUT)

reset = False

print("---- Setting Up Commands ----")
if reset == True:
    resetScanner()

#ttlMode()
motionOn()
qrModeOn()
motionSense(50)
lightsOff()

rxData = bytes()
# This is for the Pi 4
piBuf = bytes()
piScan = bytes()
piCode = ''
# This holds the QR code recieved from scanner
qrCode = '' 
# This is used to check bytes from the RX
scanByte = bytes()
# This is our scan flag
scan = 0
# Recent unlock flag
unlock = 0

print("---- Entering Infinite Loop ----")
while True:

                
        
    # Listen on UART 0 for Scanner
    if uart0.any() > 0:
        #print("---- From Scanner ----\n")
        # Bring the LED on Pico high
        led.value(1)
        # Read a byte from rx
        scanByte = uart0.read(1)
        # Put the scanned byte into the rxData
        if scanByte == b'\x06':
            print("Command overflow, throwing away")
        else:
            rxData += scanByte
        # Wait a bit
        time.sleep(0.1)
        # Bring the LED on Pico low
        led.value(0)
        
        
        # byte \r means end of scan
        if scanByte == b'\r':
            print("\n---- END OF SCAN ----")
            qrCode = rxData.decode("utf-8")
            
            # Debugging prints
            #print(rxData)
            print(qrCode)
            
            print("---- Sending to PI ----")
            # Send data to PI Master
            print(rxData)
            uart1.write(rxData)
            servo_lock(0)
            time.sleep(2)
            servo_lock(110)
            
            
            # Reset the variables
            # Do not reset the scan flag here, it messes up the locking and unlocking 
            rxData = b''
            scanByte = b''
            time.sleep(0.1)

