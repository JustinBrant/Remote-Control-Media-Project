#!/usr/bin/env python

# Basic imports
from ctypes import *
import os
import sys
import math
import time

# Phidget specific imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, IRCodeEventArgs, IRLearnEventArgs, IRRawDataEventArgs
from Phidgets.Devices.IR import IR, IRCode, IRCodeInfo, IRCodeLength, IREncoding

#=======================================================================================
# File I/O

# Initialize storage variables
irFileHeader = ""
irCommands = []
irCommandCodeInfo = []

NUM_CODES = 8
commandNames = ["Volume Up", "Volume Down", "HDMI Cycle", "Channel Up",
                "Channel Down", "TV On/Off", "Mute", "Extra"]

numLinesOriginalFile = 0

# Counts the number of lines in a file
# If the last line is empty, the count will be off by one
def countLines(filename):
    f = open(filename, "r")
    for numLines, l in enumerate(f, 1):
        pass
    f.close()
    return numLines

# Read IR commands file, store info in separate blocks for each command
def readCommandInfo():
    global irFileHeader
    global irCommands
    global irCommandCodeInfo

    # Try to open
    try:
        irFile = open("MediaProject_IR_Commands.py")
    except Exception as e:
        print("Error: Unable to open MediaProject_IR_Commands.py")
        raise e
    
    # Read header - first 4 lines
    for i in range(0, 4):
        irFileHeader += irFile.readline()

    # Read all code data
    for i in range(0, NUM_CODES):
        irCommands.append(irFile.readline())
        temp = ""
        for j in range(0, 13):
            temp += irFile.readline()
        irCommandCodeInfo.append(temp)
        irFile.readline() # Blank line between blocks
    
    # Close file
    irFile.close()

# Append original saved command to temp file
# index is for the commandNames[] list
# A blank line will be written before the command block if prependBlankline is true
def writeOriginalCommandBlock(index, prependBlankline, setToNone = False):
    irFile = open("tempIRCommands", "a")
    if (prependBlankline):
        irFile.write("\n")

    if (setToNone):
        varName = "IR_COMMAND_%s" % commandNames[index].upper().replace(" ", "_").replace("/", "")
        irFile.write("%s = \"NONE\"\n" % varName)
    else:
        irFile.write(irCommands[index])
    
    irFile.write(irCommandCodeInfo[index])
    irFile.close()

# Append last learned code info to temp file
# index is for the commandNames[] list
# A blank line will be written before the command block if prependBlankline is true
def writeNewCommandBlock(index, prependBlankline):
    irFile = open("tempIRCommands", "a")
    if (prependBlankline):
        irFile.write("\n")

    varName = "IR_COMMAND_%s" % commandNames[index].upper().replace(" ", "_").replace("/", "")
    irFile.write("%s = \"%s\"\n" % (varName, ir.getLastLearnedCode().Code.toString()))
    ci = ir.getLastLearnedCode().CodeInfo
    varName = "%s_CODE_INFO" % varName
    irFile.write("%s = IRCodeInfo()\n" % varName)
    irFile.write("%s.BitCount = %s\n" % (varName, ci.BitCount))
    irFile.write("%s.Encoding = IREncoding.%s\n" % (varName, IREncoding.toString(ci.Encoding)))
    irFile.write("%s.Length = IRCodeLength.%s\n" % (varName, IRCodeLength.toString(ci.Length)))
    irFile.write("%s.Gap = %s\n" % (varName, ci.Gap))
    irFile.write("%s.Trail = %s\n" % (varName, ci.Trail))
    
    if (ci.Header is None):
        irFile.write("%s.Header = None\n" % varName)
    else:
        irFile.write("%s.Header = [%s, %s]\n" % (varName, ci.Header[0], ci.Header[1]))
    
    irFile.write("%s.One = [%s, %s]\n" % (varName, ci.One[0], ci.One[1]))
    irFile.write("%s.Zero = [%s, %s]\n" % (varName, ci.Zero[0], ci.Zero[1]))

    if (ci.Repeat is None):
        irFile.write("%s.Repeat = None\n" % varName)
    else:
        repeatStr = "["
        for i in range(len(ci.Repeat)):
            if i > 0:
                repeatStr += ", "
            repeatStr += str(ci.Repeat[i])
        repeatStr += "]"
        irFile.write("%s.Repeat = %s\n" % (varName, repeatStr))

    if (ci.MinRepeat > 2):
        irFile.write("%s.MinRepeat = %s\n" % (varName, ci.MinRepeat))
    else:
        irFile.write("%s.MinRepeat = 2\n" % varName)
    
    irFile.write("%s.CarrierFrequency = %s\n" % (varName, ci.CarrierFrequency))
    irFile.write("%s.DutyCycle = %s\n" % (varName, ci.DutyCycle))
    
    irFile.close()

#=======================================================================================
# IR device events

irAttached = False
learnDisplayEnabled = False
codeLearned = False

def irAttachedEvent(e):
    global irAttached
    irAttached = True
    print("IR %i attached" % (e.device.getSerialNum()))

def irDetachedEvent(e):
    global irAttached
    irAttached = False
    print("IR %i detached" % (e.device.getSerialNum()))

def irLearnReceived(e):
    global codeLearned
    if (learnDisplayEnabled):
        print("Learned code: %s" % e.code.toString())
    codeLearned = True

#=======================================================================================
# Main code

# IR object
ir = IR()
ir.setOnAttachHandler(irAttachedEvent)
ir.setOnDetachHandler(irDetachedEvent)
ir.setOnIRLearnHandler(irLearnReceived)
ir.openPhidget()

# Attach IR phidget
try:
    while (not irAttached):
        try:
            ir.waitForAttach(1000)
        except PhidgetException as e:
            print("Cannot connect to IR blaster. Please ensure all devices are plugged in.")
except:
    print("\nExited.")
    exit()

# Delete MediaProject_IR_Commands.pyc file if it exists
try:
    os.remove("MediaProject_IR_Commands.pyc")
except:
    pass

# Read IR commands file, store info in separate blocks for each command
try:
    readCommandInfo()
    numLinesOriginalFile = countLines("MediaProject_IR_Commands.py")
except:
    print("Error: Unable to read IR commands file")
    exit()

# Delete temp file if it exists
try:
    os.remove("tempIRCommands")
except:
    pass

# Create temp file and write header
try:
    irFile = open("tempIRCommands", "w")
except:
    print("Error: Unable to create temp file")
    exit()

try:
    irFile.write(irFileHeader)
except:
    print("Error: Unable to write to temp file")
    irFile.close()
    exit()

irFile.close()

try:
    # Iterate through commands
    for cmd in range(0, NUM_CODES):
        print("\nCurrent command: %s" % commandNames[cmd])
        print("Press N to set to None, E to Edit, S to Skip, F to Finish and save, or C to Cancel and discard all changes:")

        # Get user input and evaluate choice
        finished = False
        while (True):
            s = raw_input("--> ")
            s = s.strip().upper()

            if (s == "N"):
                # None - Disable button by setting command to NONE
                prependBlankLine = False if (cmd == 0) else True
                writeOriginalCommandBlock(cmd, prependBlankLine, True)
                print("Command set to NONE.")
                break
            
            elif (s == "E"):
                # Edit - Prompt then wait for code to be learned
                while (True):
                    print("Press and hold the %s button while aiming the remote at the IR phidget.\n" % commandNames[cmd])
                    codeLearned = False
                    learnDisplayEnabled = True
                    while (not codeLearned):
                        time.sleep(0.01)
                    learnDisplayEnabled = False

                    # Confirm if user wants to accept code
                    codeAcceptedByUser = False
                    print("Would you like to accept this code or enter a new one?")
                    print("Press A to Accept or E to Edit:")
                    while (True):
                        s2 = raw_input("--> ")
                        s2 = s2.strip().upper()
                        if (s2 == "A"):
                            codeAcceptedByUser = True
                            break
                        
                        elif (s2 == "E"):
                            break

                    if (codeAcceptedByUser):
                        break

                prependBlankLine = False if (cmd == 0) else True
                writeNewCommandBlock(cmd, prependBlankLine)
                print("Code info written to temp file.")
                break
            
            elif (s == "S"):
                # Skip - Write original saved block for current command to temp file
                prependBlankLine = False if (cmd == 0) else True
                writeOriginalCommandBlock(cmd, prependBlankLine)
                print("Command skipped.")
                break
            
            elif (s == "F"):
                # Finish - Write all remaining original saved blocks to temp file
                for i in range(cmd, NUM_CODES):
                    prependBlankLine = False if (i == 0) else True
                    writeOriginalCommandBlock(i, prependBlankLine)
                finished = True
                break
            
            elif (s == "C"):
                # Cancel - discard changes and quit
                try:
                    os.remove("tempIRCommands")
                except:
                    pass
                print("Cancelled - changes discarded.")
                exit()
        
        if (finished):
            break

    # Check that temp file has exactly the same number of lines as original
    if (numLinesOriginalFile != countLines("tempIRCommands")):
        print("Error: File length mismatch!")
        exit()

    # Delete original file
    try:
        os.remove("MediaProject_IR_Commands.py")
    except:
        pass
    
    # Rename temp to original's name
    try:
        os.rename("tempIRCommands", "MediaProject_IR_Commands.py")
    except:
        print("Error: Unable to rename temp file!")
        exit()

    print("\nSettings saved successfully!\n")
    
except KeyboardInterrupt:
    print("\nExited without saving.\n")
    exit()
    
except Exception as e:
    print("\nRuntime exception!")
    print type(e)
    print e.args
    exit()
