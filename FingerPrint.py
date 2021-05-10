#!/usr/bin/env python3.5
# -*- coding:utf-8 -*-

import serial
import time
import threading
import sys
import RPi.GPIO as GPIO

TRUE         =  1
FALSE        =  0

# Basic response message definition
ACK_SUCCESS           = 0x00
ACK_FAIL              = 0x01
ACK_FULL              = 0x04
ACK_NO_USER           = 0x05
ACK_TIMEOUT           = 0x08
ACK_GO_OUT            = 0x0F     # The center of the fingerprint is out of alignment with sensor
ACK_USER_OCCUPIED     = 0x06
ACK_FINGER_OCCUPIED   = 0x07

# User information definition
ACK_ALL_USER          = 0x00
ACK_GUEST_USER        = 0x01
ACK_NORMAL_USER       = 0x02
ACK_MASTER_USER       = 0x03

USER_MAX_CNT          = 1000        # Maximum fingerprint number

# Command definition
CMD_HEAD              = 0xF5
CMD_TAIL              = 0xF5
CMD_ADD_1             = 0x01
CMD_ADD_2             = 0x02
CMD_ADD_3             = 0x03
CMD_MATCH             = 0x0C
CMD_DEL               = 0x04
CMD_DEL_ALL           = 0x05
CMD_USER_CNT          = 0x09
CMD_COM_LEV           = 0x28
CMD_LP_MODE           = 0x2C
CMD_TIMEOUT           = 0x2E
CMD_GET_SERIALNO      = 0x2A
CMD_FINGER_DETECTED   = 0x14
CMD_ADD_EIGEN         = 0x06
CMD_GET_EIGEN         = 0x31
CMD_GET_IMAGE         = 0x24

# GPIO Designator
Finger_WAKE_Pin   = 23
Finger_RST_Pin    = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Finger_WAKE_Pin, GPIO.IN)  
GPIO.setup(Finger_RST_Pin, GPIO.OUT) 
GPIO.setup(Finger_RST_Pin, GPIO.OUT, initial=GPIO.HIGH)

g_rx_buf            = []
PC_Command_RxBuf    = []
Finger_SleepFlag    = 0

#rLock = threading.RLock()
ser = serial.Serial("/dev/ttyS0", 19200)


def  TxAndRxCmd(command_buf, rx_bytes_need, timeout):
    global g_rx_buf
    CheckSum = 0
    tx_buf = []
    tx = ""
	
    tx_buf.append(CMD_HEAD)         
    for byte in command_buf:
        tx_buf.append(byte)  
        CheckSum ^= byte
        
    tx_buf.append(CheckSum)  
    tx_buf.append(CMD_TAIL)  
	
    # for i in tx_buf:
        # tx += chr(i)
        
    ser.flushInput()
    ser.write(bytearray(tx_buf))
    
    g_rx_buf = [] 
    time_before = time.time()
    time_after = time.time()
    while time_after - time_before < timeout and len(g_rx_buf) < rx_bytes_need:  # Waiting for response
        bytes_can_recv = ser.inWaiting()
        if bytes_can_recv != 0:
            g_rx_buf += ser.read(bytes_can_recv)    
        time_after = time.time()
        
    # for i in range(len(g_rx_buf)):
        # g_rx_buf[i] = ord(g_rx_buf[i])

    if len(g_rx_buf) != rx_bytes_need:
        return ACK_TIMEOUT
    if g_rx_buf[0] != CMD_HEAD:   	
        return ACK_FAIL
    if g_rx_buf[rx_bytes_need - 1] != CMD_TAIL:
        return ACK_FAIL
    if g_rx_buf[1] != tx_buf[1]:     
        return ACK_FAIL

    CheckSum = 0
    for index, byte in enumerate(g_rx_buf):
        if index == 0:
            continue
        if index == 6:
            if CheckSum != byte:
                return ACK_FAIL
        CheckSum ^= byte       
    return  ACK_SUCCESS;
    
#***************************************************************************
# @brief    bytes to int
#***************************************************************************/    
    def BytesToInt(bytes):
        result = 0
        for b in bytes:
            result = result * 256 + int(b)
        return result
#***************************************************************************
# @brief    int to bytes
#***************************************************************************/
def IntToBytes(value,length):
    result = []
    for i in range(0, length):
        result.append(value >> (i * 8) & 0xff)
    result.reverse()
    return result
#***************************************************************************
# @brief    bytes to int
#***************************************************************************/    
def BytesToInt(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result
#***************************************************************************
# @brief    bytes to hexs
#***************************************************************************/ 
def BytesToHex(bytes):
    # using join() + format()
    # Converting bytearray to hexadecimal string
    res = ''.join(format(x, '02x') for x in bytes)
    print("[" + str(res) + "]")
#***************************************************************************
# @brief    BytesToString
#***************************************************************************/  
def BytesToString(bytes):
    string = ''
    for b in bytes:
        string += chr(b)
    return string
#***************************************************************************
# @brief    StringToBytes
#***************************************************************************/ 
def StringToBytes(string):
    bytes = []
    for s in range(len(string)):
        bytes.append(string[s])
    return bytes
#***************************************************************************
# @brief    Get Compare Level
#***************************************************************************/    
def GetCompareLevel():
    global g_rx_buf
    command_buf = [CMD_COM_LEV, 0, 0, 1, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF	
#***************************************************************************
# @brief    Set Compare Level,the default value is 5, 
#           can be set to 0-9, the bigger, the stricter
#***************************************************************************/
def SetCompareLevel(level):
    global g_rx_buf
    command_buf = [CMD_COM_LEV, 0, level, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)   
       
    if r == ACK_TIMEOUT:
        print('timeout')
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:	
        print('successfully')
        return  g_rx_buf[3]
    else:
        print('failed')
        return 0xFF
#***************************************************************************
# @brief   Query the number of existing fingerprints
#***************************************************************************/
def GetUserCount():
    global g_rx_buf
    command_buf = [CMD_USER_CNT, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    id = []
    id.append(g_rx_buf[2])
    id.append(g_rx_buf[3])
    
    user_id = BytesToInt(id)
    print("Byets :",str(id))
    print("Byets :",str(user_id))
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return user_id
    else:
        return 0xFF
#***************************************************************************
# @brief   Get the time that fingerprint collection wait timeout
#***************************************************************************/        
def GetTimeOut():
    global g_rx_buf
    command_buf = [CMD_TIMEOUT, 0, 0, 1, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF
#***************************************************************************
# @brief    Getreservation
#***************************************************************************/
def CheckId(id,permission):
    global g_rx_buf
    b = bytearray(id.to_bytes(2, 'big'))
    high8bit = b[0]
    low8bit = b[1]
    command_buf = [CMD_ADD_1, high8bit, low8bit, permission, 0]
    r = TxAndRxCmd(command_buf, 8, 6)
    if r == ACK_SUCCESS:
        ACK_RESPONSE = g_rx_buf[4]
    if r != ACK_SUCCESS:
        return r
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        return ACK_SUCCESS
        
    return ACK_RESPONSE
#***************************************************************************
# @brief    Register fingerprint - select
#***************************************************************************/
def AddUser(permission):
    global g_rx_buf
    ACK_RESPONSE = 255
    ID = 0
    #PHASE 1
    for id in range(1,3001):
        b = IntToBytes(id,2)
        high8bit = b[0]
        low8bit = b[1]
        ACK_RESPONSE = CheckId(id,permission)
        if ACK_RESPONSE != ACK_USER_OCCUPIED and ACK_RESPONSE == ACK_SUCCESS:
            ID = id
            break
        elif ACK_RESPONSE == ACK_FINGER_OCCUPIED:break
        elif ACK_RESPONSE == ACK_FULL:break
        elif ACK_RESPONSE == ACK_FAIL:break
        elif ACK_RESPONSE == ACK_TIMEOUT:break
        
    b = bytearray(ID.to_bytes(2, 'big'))
    high8bit = b[0]
    low8bit = b[1]
 
    #PHASE 2
    if ACK_RESPONSE == ACK_SUCCESS:
        print('Phase 1 success')
        command_buf = [CMD_ADD_2, high8bit, low8bit, permission, 0]
        r = TxAndRxCmd(command_buf, 8, 6)
        ACK_RESPONSE = g_rx_buf[4]
        if r != ACK_SUCCESS:
            return r
        if ACK_RESPONSE != ACK_SUCCESS:
            return ACK_RESPONSE
            
    #PHASE 3
    if ACK_RESPONSE == ACK_SUCCESS:
        print('Phase 2 success')
        command_buf = [CMD_ADD_3, high8bit, low8bit, permission, 0]
        r = TxAndRxCmd(command_buf, 8, 6)
        ACK_RESPONSE = g_rx_buf[4]
        if r != ACK_SUCCESS:
            return r
        if ACK_RESPONSE != ACK_SUCCESS:
            return ACK_RESPONSE
            
    if ACK_RESPONSE == ACK_SUCCESS:
        print('Phase 3 success, ID:',ID) 
        return ACK_RESPONSE
        
    return ACK_RESPONSE
#***************************************************************************
# @brief    Clear fingerprints 
#***************************************************************************/
def ClearAllUser():
    global g_rx_buf
    command_buf = [CMD_DEL_ALL, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 5)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:  
        return ACK_SUCCESS
    else:
        return ACK_FAIL
#***************************************************************************
# @brief    Check if user ID is between 1 and 3
#***************************************************************************/         
def IsMasterUser(user_id):
    if user_id == 1 or user_id == 2 or user_id == 3: 
        return TRUE
    else: 
        return FALSE
#***************************************************************************
# @brief    Fingerprint matching
#***************************************************************************/        
def VerifyUser():
    global g_rx_buf
    id = []
    command_buf = [CMD_MATCH, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 5);
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and IsMasterUser(g_rx_buf[4]) == TRUE:
        id.append(g_rx_buf[2])
        id.append(g_rx_buf[3])
        user_id = BytesToInt(id)
        print("User Id :",user_id)
        return ACK_SUCCESS
    elif g_rx_buf[4] == ACK_NO_USER:
        return ACK_NO_USER
    elif g_rx_buf[4] == ACK_TIMEOUT:
        return ACK_TIMEOUT
    else:
        return ACK_GO_OUT   # The center of the fingerprint is out of alignment with sensor
#***************************************************************************
# @brief   Query serial no
#***************************************************************************
def GetSerialNumber():
    global g_rx_buf
    serial_no = []
    command_buf = [CMD_GET_SERIALNO,0,0,0,0]
    r = TxAndRxCmd(command_buf,8,5)
    if len(g_rx_buf) == 8:
        for i in range(3):
            serial_no.append(g_rx_buf[i+2])            
        
        print(serial_no)    
        return ACK_SUCCESS
    else:
        return ACK_FAIL
#***************************************************************************
# @brief    Delet user base on id 
#***************************************************************************/  
def DeleteUser(user_id):
    global g_rx_buf
    r = GetUserCount()
    if r == 0 :
        return ACK_NO_USER
    b = bytearray(user_id.to_bytes(2, 'big'))
    ID_HIGH = b[0]
    ID_LOW = b[1]
    command_buf = [CMD_DEL,ID_HIGH,ID_LOW,0,0]
    r = TxAndRxCmd(command_buf,8,5)
    if r == ACK_FAIL:
        return ACK_FAIL
    if r == ACK_SUCCESS:
        ACK_RESPONSE = g_rx_buf[4]
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        return ACK_SUCCESS
    return ACK_RESPONSE
#***************************************************************************
# @brief    Analysis the command from PC terminal
#***************************************************************************/  
def AddUserAndEigen():
    global g_rx_buf
    ACK_RESPONSE = 0
    r = GetUserCount()
    
    if r >= USER_MAX_CNT:
        return ACK_FULL	
    b = bytearray(r.to_bytes(2, 'big'))
    high8bit = b[0]
    low8bit = b[1]
    
    #Phase 1
    command_buf = [CMD_ADD_1, high8bit, low8bit + 1, 3, 0]
    r = TxAndRxCmd(command_buf, 8, 6)
    ACK_RESPONSE = g_rx_buf[4]
    if r != ACK_SUCCESS:
        return r
    
    if ACK_RESPONSE != ACK_SUCCESS:
        return ACK_RESPONSE
    print('Phase 1 success')
    #Phase 2
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        command_buf[0] = CMD_ADD_2
        r = TxAndRxCmd(command_buf, 8, 6)
        if r == ACK_SUCCESS:
            ACK_RESPONSE = g_rx_buf[4]
        if r != ACK_SUCCESS:
            return r
        if ACK_RESPONSE != ACK_SUCCESS:
            return ACK_RESPONSE
              
    print('Phase 2 success')
    #Phase 3
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        command_buf[0] = CMD_ADD_EIGEN
        r = TxAndRxCmd(command_buf, 207, 6)
        ACK_RESPONSE = g_rx_buf[4]
        eigen_value = []
        if r != ACK_SUCCESS:
            return r
        if ACK_RESPONSE != ACK_SUCCESS:
            print('Phase 3 success')
            return ACK_RESPONSE
            
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        for i in range(12,193):
            eigen_value.append(g_rx_buf[i])
        BytesToHex(eigen_value)
        return ACK_SUCCESS
        
    return ACK_FAIL
#***************************************************************************/
# @brief    Get Eigent form reader
#***************************************************************************/ 
def GetEigenById(id):
    global g_rx_buf
    eigen_values = []
    ID = IntToBytes(int(id),2)
    high8bit = ID[0]
    low8bit = ID[1]
    command_buf = [CMD_GET_EIGEN, high8bit, low8bit, 0, 0]
    r = TxAndRxCmd(command_buf, 207, 6)
    print("full data :", g_rx_buf)
    if r == ACK_SUCCESS:
        ACK_RESPONSE = g_rx_buf[4]
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        for i in range(193):
            eigen_values.append(g_rx_buf[i + 12])
        print("Eigent: ", eigen_values)
        BytesToHex(eigen_values)
        return ACK_SUCCESS
    return ACK_RESPONSE
#***************************************************************************
# @brief    Analysis the command from PC terminal
#***************************************************************************/ 
def GetImage():
    global g_rx_buf
    image = []
    command_buf = [CMD_GET_IMAGE, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 9811, 50)
    ACK_RESPONSE = g_rx_buf[4]
    if r == ACK_SUCCESS and ACK_RESPONSE == ACK_SUCCESS:
        for i in range(12,9800):
            image.append(i)
        BytesToHex(eigen_values)
    if r != ACK_SUCCESS:
       return r
    return ACK_RESPONSE
#***************************************************************************
# @brief    Analysis the command from PC terminal
#***************************************************************************/       
def Analysis_PC_Command(command):
    global Finger_SleepFlag
    
    if  command == "CMD1" and Finger_SleepFlag != 1:
        print ("Number of fingerprints already available:  %d"  % GetUserCount())
    elif command == "CMD2" and Finger_SleepFlag != 1:
        print ("Add fingerprint  (Put your finger on sensor until successfully/failed information returned) ")
        p = input("Please insert permission 1,2,3 :")
        permission = int(p)
        if IsMasterUser(permission):
            r = AddUser(permission)
            if r == ACK_SUCCESS:
                print ("Fingerprint added successfully !")
            elif r == ACK_FAIL:
                print ("Failed: Please try to place the center of the fingerprint flat to sensor")
            elif r == ACK_FINGER_OCCUPIED:
                print ("This fingerprint already exists !")
            elif r == ACK_USER_OCCUPIED:
                print ("This id has been exists !")
            elif r == ACK_FULL:
                print ("Failed: The fingerprint library is full !")      
            else:
                print ("Failed:",r)
        else:
            print("Permission not valid")
    elif command == "CMD3" and Finger_SleepFlag != 1:
        print ("Waiting Finger......Please try to place the center of the fingerprint flat to sensor !")
        r = VerifyUser()
        if r == ACK_SUCCESS:
            print ("Matching successful !")
        elif r == ACK_NO_USER:
            print ("Failed: This fingerprint was not found in the library !")
        elif r == ACK_TIMEOUT:
            print ("Failed: Time out !")
        elif r == ACK_GO_OUT:
            print ("Failed: Please try to place the center of the fingerprint flat to sensor !")
    elif command == "CMD4" and Finger_SleepFlag != 1:
        ClearAllUser()
        print ("All fingerprints have been cleared !")
    elif command == "CMD5" and Finger_SleepFlag != 1:
        GPIO.output(Finger_RST_Pin, GPIO.LOW)
        Finger_SleepFlag = 1
        print ("Module has entered sleep mode: you can use the finger Automatic wake-up function, in this mode, only CMD6 is valid, send CMD6 to pull up the RST pin of module, so that the module exits sleep !")
    elif command == "CMD6": 
        Finger_SleepFlag = 0
        GPIO.output(Finger_RST_Pin, GPIO.HIGH)
        print ("The module is awake. All commands are valid !")
    elif command == "CMD7":
        r = GetSerialNumber()
        if r == ACK_SUCCESS:
            print("This is device serial number")
        if r == ACK_FAIL:
            print("Failed: Please try again")
    elif command == "CMD8":
        id = input("Please insert id no : ")
        user_id = int(id)
        r = DeleteUser(user_id)
        if r == ACK_NO_USER:
            print("No user found")
        if r == ACK_SUCCESS:
            print("User " + id + " was deleted")
        if r == ACK_FAIL:
            print("Failed " + id + " user not deleted")
    elif command == "CMD9":
        print ("Add fingerprint  (Put your finger on sensor until successfully/failed information returned) ")
        r = AddUserAndEigen()
        if r == ACK_SUCCESS:
            print ("Fingerprint added successfully !")
        elif r == ACK_FAIL:
            print ("Failed: Please try to place the center of the fingerprint flat to sensor")
        elif r == ACK_FINGER_OCCUPIED:
            print ("This fingerprint already exists !")
        elif r == ACK_USER_OCCUPIED:
            print ("This id has been exists !")
        elif r == ACK_FULL:
            print ("Failed: The fingerprint library is full !")    
    elif command == 'CMD10':
        id = input("Please insert id no : ")
        user_id = int(id)
        r = GetEigenById(id)
        if r == ACK_SUCCESS:
            print ("Eigent successfully generated !")
        elif r == ACK_TIMEOUT:
            print ("Failed !, timeout")
        elif r == ACK_FAIL:
            print ("Failed !, please try again")
        elif r == ACK_NO_USER:
            print ("No user")
    elif command == "CMD11":
        print("Plase put your finger on sensor")
        r = GetImage()
        if r == ACK_TIMEOUT:
            print ("Failed !, timeout")
        elif r == ACK_FAIL:
            print ("Failed !, please try again")
    else:
        print ("commands are invalid !")       
#***************************************************************************
# @brief   If you enter the sleep mode, then open the Automatic wake-up function of the finger,
#         begin to check if the finger is pressed, and then start the module and match
#***************************************************************************/
def Auto_Verify_Finger():
    while True:    
        # If you enter the sleep mode, then open the Automatic wake-up function of the finger,
        # begin to check if the finger is pressed, and then start the module and match
        if Finger_SleepFlag == 1:     
            if GPIO.input(Finger_WAKE_Pin) == 1:   # If you press your finger  
                time.sleep(0.01)
                if GPIO.input(Finger_WAKE_Pin) == 1: 
                    GPIO.output(Finger_RST_Pin, GPIO.HIGH)   # Pull up the RST to start the module and start matching the fingers
                    time.sleep(0.25)	   # Wait for module to start
                    print ("Waiting Finger......Please try to place the center of the fingerprint flat to sensor !")
                    r = VerifyUser()
                    if r == ACK_SUCCESS:
                        print ("Matching successful !")
                    elif r == ACK_NO_USER:
                        print ("Failed: This fingerprint was not found in the library !")
                    elif r == ACK_TIMEOUT:
                        print ("Failed: Time out !")
                    elif r == ACK_GO_OUT:
                        print ("Failed: Please try to place the center of the fingerprint flat to sensor !")
                            
                    #After the matching action is completed, drag RST down to sleep
                    #and continue to wait for your fingers to press
                    GPIO.output(Finger_RST_Pin, GPIO.LOW)
        time.sleep(0.2)
    
def main():
   
    GPIO.output(Finger_RST_Pin, GPIO.LOW)
    time.sleep(0.25) 
    GPIO.output(Finger_RST_Pin, GPIO.HIGH)
    time.sleep(0.25)    # Wait for module to start
    while SetCompareLevel(5) != 5:                 
        print ("***ERROR***: Please ensure that the module power supply is 3.3V or 5V, the serial line connection is correct.")
        time.sleep(1)  
    print ("***************************** WaveShare Capacitive Fingerprint Reader Test *****************************")
    print ("Compare Level:  5    (can be set to 0-9, the bigger, the stricter)")
    print ("Number of fingerprints already available:  %d "  % GetUserCount())
    print (" send commands to operate the module: ")
    print ("  CMD1  : Query the number of existing fingerprints")
    print ("  CMD2  : Registered fingerprint  (Put your finger on the sensor until successfully/failed information returned) ")
    print ("  CMD3  : Fingerprint matching  (Send the command, put your finger on sensor) ")
    print ("  CMD4  : Clear fingerprints ")
    print ("  CMD5  : Switch to sleep mode, you can use the finger Automatic wake-up function (In this state, only CMD6 is valid. When a finger is placed on the sensor,the module is awakened and the finger is matched, without sending commands to match each time. The CMD6 can be used to wake up) ")
    print ("  CMD6  : Wake up and make all commands valid ")
    print ("  CMD7  : Get serial numbe")
    print ("  CMD8  : Delete user by id")
    print ("  CMD9  : Add users and upload eigenvalues")
    print ("  CMD10 : Get users eigenvalues")
    print ("  CDM11 : Get Image")
    print ("***************************** WaveShare Capacitive Fingerprint Reader Test ***************************** ")

    t = threading.Thread(target=Auto_Verify_Finger)
    t.setDaemon(True)
    t.start()
    
    while  True:     
        str = input("Please input command (CMD1-CMD10):")
        Analysis_PC_Command(str)
		
if __name__ == '__main__':
        try:
            main()
        except KeyboardInterrupt:
            if ser != None:
                ser.close()               
            GPIO.cleanup()
            print("\n\n Test finished ! \n") 
            sys.exit()
