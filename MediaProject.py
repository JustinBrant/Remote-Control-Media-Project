#!/usr/bin/env python

# Main config settings
import MediaProjectConfig as uc  # "User Config"
import MediaProject_IR_Commands as ic  # "IR Commands"

# Basic imports
from ctypes import *
import sys
import time
import RPi.GPIO as GPIO

# wiringpi for hardware PWM
import wiringpi

# Phidget imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, IRCodeEventArgs, EncoderPositionChangeEventArgs
from Phidgets.Devices.IR import IR, IRCode, IRCodeInfo, IRCodeLength, IREncoding
from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.Devices.Encoder import Encoder

#=======================================================================================
# Buttons

# Button LED pin - Must be GPIO 18 to use hardware PWM
PWM_LED_PIN = 18

# Setup wiringPi and LED pin
wiringpi.wiringPiSetupGpio()
wiringpi.pinMode(PWM_LED_PIN, 2)

# Activity timer - Buttons dim after uc.ButtonDimTimeoutSeconds seconds
lastActiveTime = time.time()

# Brightness flags
ledsDimmed = False # True = dim, False = on
ledState = [ True, True, True, True, True, True ] # True = on, False = off

# User interface has 6 buttons
buttonPressed = [ False, False, False, False, False, False ]
buttonPressedTime = [ 0, 0, 0, 0, 0, 0 ]

# Buttons class uses buttonPressed array indices
class Buttons:
    HDMI = uc.Button_HDMI
    CHANNELUP = uc.Button_ChannelUp
    CHANNELDOWN = uc.Button_ChannelDown
    ONOFF = uc.Button_TvOnOff
    MUTE = uc.Button_Mute
    EXTRA = uc.Button_Extra

# Convert from Buttons index (InterfaceKit) to array index (buttonPressed) - Depends on wiring
# InterfaceKit indices from top to bottom of user interface are: 7, 6, 5, 4, 3, 2
def InterfaceKitToButtonArrayIndex(i):
    return i - 2

# Gets index of InterfaceKit output to control specified button's LED - Depends on wiring
def ButtonLedIndex(button):
    return button - 1

# Sets state of specified button's LED
# Example: SetButtonLED(Buttons.HDMI, True)
def SetButtonLED(button, state):
    global ledState
    
    if ((button < 0) or (button >= len(buttonPressed))):
        print("Error: SetButtonLED: Button index out of range: %i" % i)
        return

    if (interfaceKitAttached):
        i = ButtonLedIndex(button)
        if ((i < 0) or (i > 7)):
            return
        
        try:
            interfaceKit.setOutputState(i, state)
        except:
            print("Error: SetButtonLED: Error setting InterfaceKit output state: %i, %s" % (i, state))
            return
            
        ledState[button] = state
    else:
        print("InterfaceKit not plugged in!")

# Sets brightness of all buttons
def SetButtonBrightness(percent):
    # Force percent to valid range
    if (percent < 0):
        percent = 0
    elif (percent > 100):
        percent = 100
    
    # Map brightness percent from 0-100 to 0-1024 for pwmWrite
    dutyCycle = (percent * 1024) / 100
    wiringpi.pwmWrite(PWM_LED_PIN, dutyCycle)

# Dims buttons to brightness set by user
def DimButtons():
    global ledsDimmed
    
    # Avoid brightness command spam
    if (not ledsDimmed):
        SetButtonBrightness(uc.ButtonBrightnessPercent_DIM)
    ledsDimmed = True

# Brightens buttons to brightness set by user
def BrightenButtons():
    global ledsDimmed
    
    # Avoid brightness command spam
    if (ledsDimmed):
        SetButtonBrightness(uc.ButtonBrightnessPercent_ON)
    ledsDimmed = False

# InterfaceKit button event
def interfaceKitInputChanged(e):
    global buttonPressed
    
    i = InterfaceKitToButtonArrayIndex(e.index)
    if ((i < 0) or (i >= len(buttonPressed))):
        return
    
    if (e.state == True):
        buttonPressed[i] = True

#=======================================================================================
# Button press actions

def ProcessButtonPress(index):
    global buttonPressedTime
    
    # Record time of button press and turn off
    if (uc.ButtonOffWhenPressedTimeSeconds > 0):
        if ((index >= 0) and (index < len(buttonPressedTime))):
            buttonPressedTime[index] = time.time()
            SetButtonLED(index, False)

    # Perform button's action
    if (index == Buttons.HDMI):
        print("HDMI cycle button pressed")
        if (ic.IR_COMMAND_HDMI_CYCLE != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_HDMI_CYCLE, ic.IR_COMMAND_HDMI_CYCLE_CODE_INFO.BitCount), ic.IR_COMMAND_HDMI_CYCLE_CODE_INFO)
            else:
                print("IR not plugged in!")
            
    elif (index == Buttons.CHANNELUP):
        print("Channel up button pressed")
        if (ic.IR_COMMAND_CHANNEL_UP != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_CHANNEL_UP, ic.IR_COMMAND_CHANNEL_UP_CODE_INFO.BitCount), ic.IR_COMMAND_CHANNEL_UP_CODE_INFO)
            else:
                print("IR not plugged in!")
        
    elif (index == Buttons.CHANNELDOWN):
        print("Channel down button pressed")
        if (ic.IR_COMMAND_CHANNEL_DOWN != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_CHANNEL_DOWN, ic.IR_COMMAND_CHANNEL_DOWN_CODE_INFO.BitCount), ic.IR_COMMAND_CHANNEL_DOWN_CODE_INFO)
            else:
                print("IR not plugged in!")
        
    elif (index == Buttons.ONOFF):
        print("TV on/off button pressed")
        if (ic.IR_COMMAND_TV_ONOFF != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_TV_ONOFF, ic.IR_COMMAND_TV_ONOFF_CODE_INFO.BitCount), ic.IR_COMMAND_TV_ONOFF_CODE_INFO)
            else:
                print("IR not plugged in!")
            
    elif (index == Buttons.MUTE):
        print("Mute button pressed")
        if (ic.IR_COMMAND_MUTE != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_MUTE, ic.IR_COMMAND_MUTE_CODE_INFO.BitCount), ic.IR_COMMAND_MUTE_CODE_INFO)
            else:
                print("IR not plugged in!")
            
    elif (index == Buttons.EXTRA):
        print("Extra button pressed")
        if (ic.IR_COMMAND_EXTRA != "NONE"):
            if (irAttached):
                ir.transmit(IRCode(ic.IR_COMMAND_EXTRA, ic.IR_COMMAND_MUTE_CODE_INFO.BitCount), ic.IR_COMMAND_MUTE_CODE_INFO)
            else:
                print("IR not plugged in!")

#=======================================================================================
# Volume control

# Reference start position for deadzone
deadzoneStartPos = 0

# Position when last volume command was sent
lastVolumeCommandPos = 0

def encoderPositionChanged(e):
    global irAttached
    global deadzoneStartPos
    global lastVolumeCommandPos
    global lastActiveTime
    
    currPos = encoder.getPosition(e.index)
    
    # Reset deadzone reference if the dial hasn't been moved for a specified time
    if (e.time > uc.DeadzoneResetTimeMilliseconds):
        deadzoneStartPos = currPos
        lastVolumeCommandPos = currPos
        
    # Send a volume command at specified intervals if out of the deadzone
    elif (abs(currPos - deadzoneStartPos) > uc.DeadzoneTicks):
        # Reset activity timer
        if (uc.VolumeDialBrightensLEDs != 0):
            lastActiveTime = time.time()
        
        # Account for volume direction setting
        diff = 0
        if (uc.PositiveVolumeDirection == "CCW"):
            diff = lastVolumeCommandPos - currPos
        else:
            diff = currPos - lastVolumeCommandPos

        # Determine whether volume went up or down
        if (abs(diff) >= uc.TicksPerVolumeCommand):
            if (diff > 0):
                print("Vol up")
                if (ic.IR_COMMAND_VOLUME_UP != "NONE"):
                    if (irAttached):
                        ir.transmit(IRCode(ic.IR_COMMAND_VOLUME_UP, ic.IR_COMMAND_VOLUME_UP_CODE_INFO.BitCount), ic.IR_COMMAND_VOLUME_UP_CODE_INFO)
                    else:
                        print("IR not plugged in!")
            else:
                print("Vol down")
                if (ic.IR_COMMAND_VOLUME_DOWN != "NONE"):
                    if (irAttached):
                        ir.transmit(IRCode(ic.IR_COMMAND_VOLUME_DOWN, ic.IR_COMMAND_VOLUME_DOWN_CODE_INFO.BitCount), ic.IR_COMMAND_VOLUME_DOWN_CODE_INFO)
                    else:
                        print("IR not plugged in!")

            # Only reset last position when a command is sent
            lastVolumeCommandPos = currPos

#=======================================================================================
# Device attachment events

irAttached = False
interfaceKitAttached = False
encoderAttached = False

def irAttachedEvent(e):
    global irAttached
    irAttached = True
    print("IR %i attached" % (e.device.getSerialNum()))

def irDetachedEvent(e):
    global irAttached
    irAttached = False
    print("IR %i detached" % (e.device.getSerialNum()))

def interfaceKitAttachedEvent(e):
    global interfaceKitAttached
    interfaceKitAttached = True
    
    # Initialize all button LEDs on
    for i in range(1, 6):
        SetButtonLED(i, True)

    print("InterfaceKit %i attached" % (e.device.getSerialNum()))

def interfaceKitDetachedEvent(e):
    global interfaceKitAttached
    interfaceKitAttached = False
    print("InterfaceKit %i detached" % (e.device.getSerialNum()))

def encoderAttachedEvent(e):
    global encoderAttached 
    encoderAttached = True
    print("Encoder %i attached" % (e.device.getSerialNum()))

def encoderDetachedEvent(e):
    global encoderAttached
    encoderAttached = False
    print("Encoder %i detached" % (e.device.getSerialNum()))

#=======================================================================================
# User config checks and initialization

# Ensure all button indices are valid
if (Buttons.HDMI < 0 or Buttons.HDMI > 5 or
    Buttons.CHANNELUP < 0 or Buttons.CHANNELUP > 5 or
    Buttons.CHANNELDOWN < 0 or Buttons.CHANNELDOWN > 5 or
    Buttons.ONOFF < 0 or Buttons.ONOFF > 5 or
    Buttons.MUTE < 0 or Buttons.MUTE > 5 or
    Buttons.EXTRA < 0 or Buttons.EXTRA > 5):
    print("Error: All button indices must be from 0 to 5 only. Please check MediaProjectConfig.")
    exit()

# Start with buttons bright and reset activity timer
SetButtonBrightness(uc.ButtonBrightnessPercent_ON)
lastActiveTime = time.time()

#=======================================================================================
# Object attachment

# IR object
ir = IR()
ir.setOnAttachHandler(irAttachedEvent)
ir.setOnDetachHandler(irDetachedEvent)
ir.openPhidget()

# Attach IR phidget
try:
    ir.waitForAttach(1000)
except PhidgetException as e:
    print("Cannot connect to IR blaster. Please ensure all devices are plugged in.")

# InterfaceKit object
interfaceKit = InterfaceKit()
interfaceKit.setOnAttachHandler(interfaceKitAttachedEvent)
interfaceKit.setOnDetachHandler(interfaceKitDetachedEvent)
interfaceKit.setOnInputChangeHandler(interfaceKitInputChanged)
interfaceKit.openPhidget()

# Attach InterfaceKit phidget
try:
    interfaceKit.waitForAttach(1000)
except PhidgetException as e:
    print("Cannot connect to InterfaceKit (for buttons). Please ensure all devices are plugged in.")

# Encoder object
encoder = Encoder()
encoder.setOnAttachHandler(encoderAttachedEvent)
encoder.setOnDetachHandler(encoderDetachedEvent)
encoder.setOnPositionChangeHandler(encoderPositionChanged)
encoder.openPhidget()

# Attach encoder object
try:
    encoder.waitForAttach(1000)
except PhidgetException as e:
    print("Cannot connect to Encoder. Please ensure all devices are plugged in.")

#=======================================================================================
# Main loop

try:
    # Reset activity timer
    lastActiveTime = time.time()

    # Begin main loop
    while (True):
        # Check for new button presses
        index = 0
        for state in buttonPressed:
            if (state == True):
                # Process button press then reset flag
                ProcessButtonPress(index)
                buttonPressed[index] = False

                # Reset activity timer
                lastActiveTime = time.time()
            index += 1

        # Dim buttons after timeout and brighten buttons when there is activity
        if ((time.time() - lastActiveTime) > uc.ButtonDimTimeoutSeconds):
            DimButtons()
        else:
            BrightenButtons()

        # Turn pressed button LEDs back on
        if (uc.ButtonOffWhenPressedTimeSeconds > 0):
            index = 0
            for t in buttonPressedTime:
                # Only check time and/or send command if LED is currently off
                if (ledState[index] == False):
                    if ((time.time() - t) > uc.ButtonOffWhenPressedTimeSeconds):
                        SetButtonLED(index, True)
                index += 1

        time.sleep(0.05)
        
except KeyboardInterrupt:
    print("\nProgram stopped.")
    
except Exception as e:
    print("\nRuntime exception!")
    print type(e)
    print e.args
    
finally:
    # Clean up GPIOs
    wiringpi.digitalWrite(PWM_LED_PIN, 0)
    wiringpi.pinMode(PWM_LED_PIN, 0)

    print("Press enter to exit...")
    raw_input()
    
    exit()
