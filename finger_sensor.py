import serial
import time
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

USER_MAX_CNT          = 3000        # Maximum fingerprint number

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
CMD_ADD_EIGEN        = 0x06
CMD_SET_SERIALNO      = 0x08
CMD_GET_EIGEN         = 0x31
CMD_QUERY_PERMISSION  = 0x0A
CMD_SET_EIGEN         = 0x41
CMD_COMPARE_EIGEN     = 0x44

# GPIO Designator
Finger_WAKE_Pin   = 23
Finger_RST_Pin    = 24

# GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Finger_WAKE_Pin, GPIO.IN)  
GPIO.setup(Finger_RST_Pin, GPIO.OUT) 
GPIO.setup(Finger_RST_Pin, GPIO.OUT, initial=GPIO.HIGH)

g_rx_buf            = []
PC_Command_RxBuf    = []

#rLock = threading.RLock()
ser = serial.Serial("/dev/ttyS0", 19200)

class SZM219(object):
#***************************************************************************
# @brief    send a long command, and wait for the response of module
#***************************************************************************/
    def  TxAndRxCmdLong(self,command_buf, command_data, rx_bytes_need, timeout):
        global g_rx_buf
        CheckSum = 0
        tx_buf = []
        CheckSumData = 0
        tx_buf_data = []
        
        # Command
        tx_buf.append(CMD_HEAD)         
        for byte in command_buf:
            tx_buf.append(byte)  
            CheckSum ^= byte
            
        tx_buf.append(CheckSum)  
        tx_buf.append(CMD_TAIL)  
                
        ser.flushInput()
        ser.write(bytearray(tx_buf))
        
        #command data
        tx_buf_data.append(CMD_HEAD)         
        for byte in command_data:
            tx_buf_data.append(byte)  
            CheckSumData ^= byte
            
        tx_buf_data.append(CheckSumData)  
        tx_buf_data.append(CMD_TAIL)  
                
        ser.flushInput()
        ser.write(bytearray(tx_buf_data))
        
        g_rx_buf = [] 
        time_before = time.time()
        time_after = time.time()
        while time_after - time_before < timeout and len(g_rx_buf) < rx_bytes_need:  # Waiting for response
            bytes_can_recv = ser.inWaiting()
            if bytes_can_recv != 0:
                g_rx_buf += ser.read(bytes_can_recv)    
            time_after = time.time()
            
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
# @brief    send a command, and wait for the response of module
#***************************************************************************/
    def TxAndRxCmd(self,command_buf, rx_bytes_need, timeout):
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
	    
        ser.flushInput()
        ser.write(bytearray(tx_buf))
        # print('data tx :', tx_buf)
        
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
            # print("Fail TxAndRxCmd: byte len")
            return ACK_TIMEOUT
        if g_rx_buf[0] != CMD_HEAD:   
            print("Fail TxAndRxCmd: CMD_HEAD")
            return ACK_FAIL
        if g_rx_buf[rx_bytes_need - 1] != CMD_TAIL:
            print("Fail TxAndRxCmd: CMD_TAIL")
            return ACK_FAIL
        if g_rx_buf[1] != tx_buf[1]: 
            print("Fail TxAndRxCmd: CMD NOT SAME")
            return ACK_FAIL

        CheckSum = 0
        for index, byte in enumerate(g_rx_buf):
            if index == 0:
                continue
            if index == 6:
                if CheckSum != byte:
                    print("Fail TxAndRxCmd: checksum")
                    return ACK_FAIL
            CheckSum ^= byte       
        return  ACK_SUCCESS
        # check : ACK_SUCCESS , ACK_FAIL , ACK_TIMEOUT
#***************************************************************************
# @brief    bytes to int
#***************************************************************************/    
    def BytesToInt(self,bytes):
        result = 0
        for b in bytes:
            result = result * 256 + int(b)
        return result
#***************************************************************************
# @brief    int to bytes
#***************************************************************************/    
    def IntToBytes(self,value,length):
        result = []
        for i in range(0, length):
            result.append(value >> (i * 8) & 0xff)
        result.reverse()
        return result
#***************************************************************************
# @brief    byte array to hex_string
#***************************************************************************/ 
    def ByteArrayToHexString(self,byte_array):
        result = ''.join(format(x, '02x') for x in byte_array)
        return result
#***************************************************************************
# @brief    hex_string to byte array 
#***************************************************************************/
    def HexStringToByteArray(self,hex_string):
        result = list(bytearray.fromhex(hex_string))
        return result
#***************************************************************************
# @brief    Get Compare Level
#***************************************************************************/    
    def  GetCompareLevel(self):
        global g_rx_buf
        response_data =[0,0]
        command_buf = [CMD_COM_LEV, 0, 0, 1, 0]
        r = self.TxAndRxCmd(command_buf, 8, 0.1)
        #********************************#
        # 0 - value                      #
        # 1 - state                      #
        #********************************#
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:	
            response_data[0] = g_rx_buf[3]
            response_data[1] = ACK_SUCCESS
            return response_data
        else:
            print('Fail: SetCompareLevel')
            if r != ACK_SUCCESS:
                response_data[1] = r
            else:
                response_data[1] = g_rx_buf[4]
            return response_data
#***************************************************************************
# @brief    Set Compare Level,the default value is 5, 
#           can be set to 0-9, the bigger, the stricter
#***************************************************************************/
    def SetCompareLevel(self,level):
        global g_rx_buf
        response_data =[0,0]
        command_buf = [CMD_COM_LEV, 0, level, 0, 0]
        r = self.TxAndRxCmd(command_buf, 8, 0.1)   
        #********************************#
        # 0 - value                      #
        # 1 - state                      #
        #********************************#
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:	
            response_data[0] = g_rx_buf[3]
            response_data[1] = ACK_SUCCESS
            return response_data
        else:
            print('Fail: SetCompareLevel')
            if r != ACK_SUCCESS:
                response_data[1] = r
            else:
                response_data[1] = g_rx_buf[4]
            return response_data
#***************************************************************************
# @brief   Query the number of existing fingerprints
#***************************************************************************/
    def GetUserCount(self):
        global g_rx_buf
        command_buf = [CMD_USER_CNT, 0, 0, 0, 0]
        r = self.TxAndRxCmd(command_buf, 8, 0.1)
        #****************************#
        #  0 - high8bit              #
        #  1 - low8bit               #
        #  2 - State                 #
        #****************************#
        total_user = [0,0,0]
        if r != ACK_SUCCESS:
            total_user[2] = r
            return total_user
        if r == ACK_SUCCESS and g_rx_buf[4] != ACK_SUCCESS:
            total_user[2] = g_rx_buf[4]
            return total_user
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            total_user[0] = g_rx_buf[2]
            total_user[1] = g_rx_buf[3]
            total_user[2] = ACK_SUCCESS
            return total_user
#***************************************************************************
# @brief   Set the time that fingerprint collection wait timeout
#***************************************************************************/        
    def SetTimeOut(self,timeout):
        global g_rx_buf
        response_data = [0,ACK_FAIL]
        command_buf = [CMD_TIMEOUT, 0, timeout, 0, 0]
        r =self.TxAndRxCmd(command_buf, 8, 0.1)
        #******************************#
        # 0 - timeout                  #
        # 1 - State                    #
        #******************************#
        if r == ACK_TIMEOUT:
            response_data[1] = r
            return response_data
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            response_data[0] = g_rx_buf[3]
            response_data[1] = ACK_SUCCESS
            return response_data
        else:
            response_data[1] = g_rx_buf[4]
            return response_data
        # Checking : ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS
#***************************************************************************
# @brief   Get the time that fingerprint collection wait timeout
#***************************************************************************/        
    def GetTimeOut(self):
        global g_rx_buf
        response_data = [0,ACK_FAIL]
        command_buf = [CMD_TIMEOUT, 0, 0, 1, 0]
        r =self.TxAndRxCmd(command_buf, 8, 0.1)
        #******************************#
        # 0 - timeout                  #
        # 1 - State                    #
        #******************************#
        if r == ACK_TIMEOUT:
            response_data[1] = r
            return response_data
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            response_data[0] = g_rx_buf[3]
            response_data[1] = ACK_SUCCESS
            # print('Timeout data: ', g_rx_buf)
            return response_data
        else:
            response_data[1] = g_rx_buf[4]
            return response_data
        # Checking : ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS
#***************************************************************************
# @brief    Get unuse user id
#***************************************************************************/
    def CheckId(self,id,permission):
        global g_rx_buf
        b = bytearray(id.to_bytes(2, 'big'))
        high8bit = b[0]
        low8bit = b[1]
        command_buf = [CMD_ADD_1, high8bit, low8bit, permission, 0]
        r = self.TxAndRxCmd(command_buf, 8, 6)
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            return ACK_SUCCESS
        if r != ACK_SUCCESS:
            print("Fail here:",r)
            return r
        if g_rx_buf[4] != ACK_SUCCESS:
            return g_rx_buf[4]
#***************************************************************************
# @brief    Add user phase1
#***************************************************************************/            
    def addUserPhase1(self,permission):
        ACK_RESPONSE = 255
        ID = 0
        add_user_data = [0,0,0]
        #***********************#
        # 0 - high8bit          #
        # 1 - low8bit           #
        # 2 - State             #
        #***********************#
        for id in range(USER_MAX_CNT):
            b = self.IntToBytes(id+1,2)
            high8bit = b[0]
            low8bit = b[1]
            ACK_RESPONSE = self.CheckId(id+1,permission)
            if ACK_RESPONSE != ACK_USER_OCCUPIED and ACK_RESPONSE == ACK_SUCCESS:
                ID = id
                break
            elif ACK_RESPONSE == ACK_FINGER_OCCUPIED:break
            elif ACK_RESPONSE == ACK_FULL:break
            elif ACK_RESPONSE == ACK_FAIL:break
            elif ACK_RESPONSE == ACK_TIMEOUT:break
            
        if ACK_RESPONSE == ACK_SUCCESS:
            # print('Phase 1 pass')
            add_user_data[0] = high8bit
            add_user_data[1] = low8bit
            add_user_data[2] = ACK_SUCCESS 
            return add_user_data
        else:
            add_user_data[2] = ACK_RESPONSE 
            return add_user_data
        # Checking : ACK_TIMEOUT, ACK_FAIL, ACK_FINGER_OCCUPIED, ACK_FULL ,ACK_SUCCESS
#***************************************************************************
# @brief    Add user phase2
#***************************************************************************/ 
    def addUserPhase2(self,user_id,permission):
        global g_rx_buf
        id = self.IntToBytes(user_id,2)
        high8bit = id[0]
        low8bit = id[1]
        command_buf = [CMD_ADD_2, high8bit, low8bit, permission, 0]
        r = self.TxAndRxCmd(command_buf, 8, 6)
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            ACK_RESPONSE = ACK_SUCCESS
            # print('Phase 2 pass')
            return ACK_SUCCESS
        else:
            if r != ACK_SUCCESS:
                return r
            if g_rx_buf[4] != ACK_SUCCESS:
                return g_rx_buf[4]
        # Checking : ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS
#***************************************************************************
# @brief    Add user phase3
#***************************************************************************/
    def addUserPhase3(self,user_id,permission):
        global g_rx_buf
        id = self.IntToBytes(user_id,2)
        high8bit = id[0]
        low8bit = id[1]
        command_buf = [CMD_ADD_3, high8bit, low8bit, permission, 0]
        r = self.TxAndRxCmd(command_buf, 8, 6)
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            # print('Phase 3 pass')
            return ACK_SUCCESS
        else:
            if r != ACK_SUCCESS:
                return r        
            if g_rx_buf[4] != ACK_SUCCESS:
                return g_rx_buf[4]
        # Checking : ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS
#***************************************************************************
# @brief    Add user
#***************************************************************************/
    def addUser(self,permission):
        user_id = [0,0]
        data_response = []
        data = [0,0,ACK_FAIL]
        ACK_STATE = 0xFF
        #*********************#
        # 0 - high8bit        #
        # 1 - low8bit         #
        # 2 - State           #
        #*********************#
        #PHASE 1
        data_response = self.addUserPhase1(permission)      
        user_id[0] = data_response[0]
        user_id[1] = data_response[1]
        ACK_STATE = data_response[2]
        id = self.BytesToInt(user_id)
        
        #PHASE 2
        if ACK_STATE != ACK_SUCCESS:
            print("PHASE 1 Fail", ACK_STATE)
            data[2] = ACK_STATE
            return data
        elif ACK_STATE == ACK_SUCCESS:  
            ACK_STATE = ACK_FAIL
            ACK_STATE = self.addUserPhase2(id,permission)
            if ACK_STATE != ACK_SUCCESS:
                print("PHASE 2 Fail", ACK_STATE)
                data[2] = ACK_STATE
                return data
            elif ACK_STATE == ACK_SUCCESS:
                ACK_STATE = ACK_FAIL
                ACK_STATE = self.addUserPhase3(id,permission)
                if ACK_STATE != ACK_SUCCESS:
                    print("PHASE 3 Fail", ACK_STATE)
                elif ACK_STATE == ACK_SUCCESS:
                    data[0] = user_id[0]
                    data[1] = user_id[1]
                    data[2] = ACK_SUCCESS
                    return data
                    
        data[2] = ACK_FAIL            
        return data       
        # checking ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS , ACK_FINGER_OCCUPIED, ACK_FULL
#***************************************************************************/
# @brief    Scand and verify Eigent
#***************************************************************************/ 
    def VerifyEigen(self,eigen_values):
        global g_rx_buf
        command_data = []
        response_data = [0,0,ACK_FAIL]

        if len(eigen_values) != 193:
            # print("SetEigenById : Failed, eigen values unvalid") 
            return response_data
            
        command_data.append(0)
        command_data.append(0)
        command_data.append(0)
            
        for e in eigen_values:
            command_data.append(e)
            
        command_buf = [CMD_COMPARE_EIGEN, 0, 196, 0, 0]
        r = self.TxAndRxCmdLong(command_buf, command_data, 8, 6)
        
        # print('Verify eigen :' , g_rx_buf)
        if r != ACK_SUCCESS:
            return r

        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            return ACK_SUCCESS
        else:
            return g_rx_buf[4]

        return ACK_TIMEOUT
#***************************************************************************/
# @brief    Set Eigent to reader
#***************************************************************************/ 
    def SetEigenById(self,id,permission,eigen_values):
        global g_rx_buf
        command_data = []
        response_data = [0,0,ACK_FAIL]
        if permission > 4 and permission < 0:
            print("SetEigenById : Failed, permission unvalid") 
            return response_data
        if len(eigen_values) != 193:
            print("SetEigenById : Failed, eigen values unvalid") 
            return response_data
        ID = self.IntToBytes(int(id),2)
        Idhigh8bit = ID[0]
        Idlow8bit = ID[1]
        #*****************************#
        # 0 - Id_High8bit             #
        # 1 - Id_Low8bit              #
        # 2 - state                   #
        #*****************************#
        command_data.append(Idhigh8bit)
        command_data.append(Idlow8bit)
        command_data.append(permission)
        for e in eigen_values:
            command_data.append(e)
        
        command_buf = [CMD_SET_EIGEN, 0, 196, 0, 0]
        r = self.TxAndRxCmdLong(command_buf, command_data, 8, 10)
        # print('SetEigenById :', g_rx_buf)
        if r != ACK_SUCCESS:
            print("SetEigenById : Failed, data received unvalid") 
            return response_data
        if r == ACK_SUCCESS:
            if g_rx_buf[4] == ACK_SUCCESS: 
                response_data[0] = g_rx_buf[2]
                response_data[1] = g_rx_buf[3]
                response_data[2] = ACK_SUCCESS
            else:
                print("SetEigenById : Failed") 
                response_data[2] = g_rx_buf[4]
                return response_data
        else:
            return response_data
#***************************************************************************/
# @brief    Get Eigent form reader
#***************************************************************************/ 
    def GetEigenById(self,id):
        global g_rx_buf
        eigen_values = []
        ID = self.IntToBytes(int(id),2)
        high8bit = ID[0]
        low8bit = ID[1]
        #*****************************#
        # 0 - 192 eigen_values        #
        # 193 - Permission            #
        # 194 - state                 #
        #*****************************#
        command_buf = [CMD_GET_EIGEN, high8bit, low8bit, 0, 0]
        r = self.TxAndRxCmd(command_buf, 207, 6)
        # print('eigen data :', g_rx_buf)
        if r != ACK_SUCCESS:
            for i in range(193):
                eigen_values.append(0)
                
            eigen_values.append(0)
            eigen_values.append(r)
            return eigen_values
                
        elif r == ACK_SUCCESS:
            if g_rx_buf[4] == ACK_SUCCESS:
                for i in range(193):
                    eigen_values.append(g_rx_buf[i + 12]) #eigen_values
                    
                eigen_values.append(g_rx_buf[11]) # permission
                eigen_values.append(ACK_SUCCESS) # state
                # print("Eigent: ", eigen_values)
                return eigen_values
            else:
                if g_rx_buf[4] != ACK_SUCCESS:
                    for i in range(193):
                        eigen_values.append(0)
                        
                    eigen_values.append(0)
                    eigen_values.append(g_rx_buf[4])
                    return eigen_values
            # checking ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS, ACK_NO_USER
#***************************************************************************
# @brief    Clear fingerprints 
#***************************************************************************/
    def ClearAllUser(self):
        global g_rx_buf
        command_buf = [CMD_DEL_ALL, 0, 0, 0, 0]
        r =self.TxAndRxCmd(command_buf, 8, 5)
        if r == ACK_TIMEOUT:
            return ACK_TIMEOUT
        if r == ACK_SUCCESS:
            if g_rx_buf[4] == ACK_SUCCESS:  
                return ACK_SUCCESS
            else:
                return g_rx_buf[4]
        else:
            return ACK_FAIL
#***************************************************************************
# @brief    Check if user ID is between 1 and 3
#***************************************************************************/         
    def IsMasterUser(self,user_id):
        if user_id == 1 or user_id == 2 or user_id == 3: 
            return TRUE
        else: 
            return FALSE
#***************************************************************************
# @brief    Fingerprint matching
#***************************************************************************/        
    def Query_Permission(self,user_id):
        global g_rx_buf
        data_response = [0,ACK_NO_USER]
        id = self.IntToBytes(user_id,2)
        command_buf = [CMD_QUERY_PERMISSION, id[0], id[1], 0, 0]
        # print('CMD_Query_Permission : ', command_buf)
        r = self.TxAndRxCmd(command_buf, 8, 5)
        #******FORMAT data_response******#
        # 0 - permission                 #
        # 1 - status                     #
        #********************************#
        # print('Query_Permission : ', g_rx_buf)
        if r != ACK_SUCCESS:
            data_response[1] = r
            return data_response
        elif r == ACK_SUCCESS:
            if self.IsMasterUser(g_rx_buf[4]) == True:
                data_response[0] = g_rx_buf[4]
                data_response[1] = ACK_SUCCESS
                return data_response
            else:
                data_response[1] = ACK_NO_USER
                return data_response    
#***************************************************************************
# @brief    Fingerprint matching
#***************************************************************************/        
    def VerifyUser(self):
        global g_rx_buf
        data_response = [0,0,0,ACK_FAIL]
        id = []
        command_buf = [CMD_MATCH, 0, 0, 0, 0]
        r = self.TxAndRxCmd(command_buf, 8, 5)
        
        #******FORMAT data_response******#
        # 0 - high8bit user id           #
        # 1 - low8bit user id            #
        # 2 - user category              #
        # 3 - status                     #
        #********************************#
        
        if r != ACK_SUCCESS:
            data_response[3] = r #3
            
        if r == ACK_SUCCESS:
            if self.IsMasterUser(g_rx_buf[4]) == TRUE:
                data_response[0] = g_rx_buf[2] #0
                data_response[1] = g_rx_buf[3] #1
                data_response[2] = g_rx_buf[4] #2
                data_response[3] = ACK_SUCCESS #3
                id.append(data_response[0])
                id.append(data_response[1])
                user_id = self.BytesToInt(id)
                # print("User Id :",user_id)
                return data_response
            else:
                data_response[3] = g_rx_buf[4]
                return data_response
       
        return data_response
        # check : ACK_SUCCESS , ACK_FAIL , ACK_TIMEOUT , ACK_NO_USER 
#***************************************************************************
# @brief   Set serial no
#***************************************************************************
    def SetSerialNumber(self,SN):
        global g_rx_buf
        serial_no = self.IntToBytes(SN,3)
        #*******************************#
        # 0 - bit 23- 16                #
        # 1 - bit 15 - 8                #
        # 2 - bit 8 - 0                 #
        # 3 - State                    #
        #*******************************#
        command_buf = [CMD_SET_SERIALNO,serial_no[0],serial_no[1],serial_no[2],0]
        r = self.TxAndRxCmd(command_buf,8,5)
        # print('Set Serial : ', g_rx_buf)
        if r ==  ACK_SUCCESS and len(g_rx_buf) == 8:
            return ACK_SUCCESS   
        return ACK_FAIL        
#***************************************************************************
# @brief   Query serial no
#***************************************************************************
    def GetSerialNumber(self):
        global g_rx_buf
        serial_no = []
        command_buf = [CMD_GET_SERIALNO,0,0,0,0]
        time.sleep(0.02)
        r = self.TxAndRxCmd(command_buf,8,5)
        #*******************************#
        # 0 - bit 23- 16                #
        # 1 - bit 15 - 8                #
        # 2 - bit 8 - 0                 #
        # 3 - State                   #
        #*******************************#
        if len(g_rx_buf) == 8:
            for i in range(3):
                serial_no.append(g_rx_buf[i+2])                    
            SN = self.BytesToInt(serial_no)
            serial_no.append(ACK_SUCCESS)
            return serial_no
        else:
            for i in range(3):
                serial_no.append(0)
            serial_no.append(ACK_FAIL)
            return serial_no
#***************************************************************************
# @brief    Delet user base on id 
#***************************************************************************/  
    def DeleteUser(self,user_id):
        global g_rx_buf
        b = bytearray(user_id.to_bytes(2, 'big'))
        ID_HIGH = b[0]
        ID_LOW = b[1]
        command_buf = [CMD_DEL,ID_HIGH,ID_LOW,0,0]
        r = self.TxAndRxCmd(command_buf,8,5)
        if r != ACK_SUCCESS:
            return ACK_FAIL
        elif r == ACK_SUCCESS:
            if g_rx_buf[4] == ACK_SUCCESS:
                return ACK_SUCCESS
                
        return ACK_FAIL
#***************************************************************************
# @brief    Analysis the command from PC terminal
#***************************************************************************/  
    def AddUsersEigen(self):
        global g_rx_buf
        #Phase 1
        data_response = []
        ACK_STATE = 0xFF
        #*************************#
        # 0~192 - eigent_values   #
        # 193   - State           #
        #*************************#
        #PHASE 1
        r = self.addUserPhase1(1)      
        ACK_STATE = r[2]
        #PHASE 2
        if ACK_STATE != ACK_SUCCESS:
            print("PHASE 1 Fail", ACK_STATE)
            for i in range(193):
                data_response.append(0) 
            data_response.append(ACK_STATE) 
            return data_response
        elif ACK_STATE == ACK_SUCCESS:  
            # print("PHASE 1 PASS")
            ACK_STATE = self.addUserPhase2(1,1)
            if ACK_STATE != ACK_SUCCESS:
                print("PHASE 2 Fail", ACK_STATE)
                for i in range(193):
                    data_response.append(0) 
                data_response.append(ACK_STATE) 
                return data_response
            elif ACK_STATE == ACK_SUCCESS:
                # print("PHASE 2 PASS")
                #Phase 3
                command_buf = [CMD_ADD_EIGEN,0,0,0,0]
                r = self.TxAndRxCmd(command_buf, 207, 6)
                ACK_STATE = g_rx_buf[4]
                if r != ACK_SUCCESS:
                    for i in range(193):
                        data_response.append(0) 
                    data_response.append(r) 
                    return data_response                    
                if r == ACK_SUCCESS and ACK_STATE == ACK_SUCCESS:
                    # print('PHASE 3 PASS')
                    for i in range(193):
                        data_response.append(g_rx_buf[i + 12]) 
                    data_response.append(ACK_SUCCESS)
                    return data_response
                else:
                    for i in range(193):
                        data_response.append(0)
                    data_response.append(r) 
                    return data_response  
#***************************************************************************
# @brief    Module Wakeup
#***************************************************************************/     
    def isWake(self):
        if GPIO.input(Finger_WAKE_Pin) == 1:
            return True
        elif GPIO.input(Finger_WAKE_Pin) == 0:
            return False
#***************************************************************************
# @brief    Module Power Disble
#***************************************************************************/  
    def powerDisable(self):
        GPIO.output(Finger_RST_Pin, GPIO.LOW)
        # print('Power Disable')
#***************************************************************************
# @brief    Module Power Enable
#***************************************************************************/  
    def powerEnable(self):
        GPIO.output(Finger_RST_Pin, GPIO.HIGH)
        # print('Power Enable')
#***************************************************************************
# @brief    Module test
#***************************************************************************/     
    def module(self):
        time.sleep(0.02)
        r = self.SetCompareLevel(5)
        if r[1] == ACK_SUCCESS and r[0] == 5:
            return ACK_SUCCESS
        else:
            return ACK_FAIL
#***************************************************************************
# @brief   If you enter the sleep mode, then open the Automatic wake-up function of the finger,
#         begin to check if the finger is pressed, and then start the module and match
#***************************************************************************/
    def Auto_Verify_Finger(self):  
        #******FORMAT data_response******#
        # 0 - high8bit user id           #
        # 1 - low8bit user id            #
        # 2 - user category              #
        # 3 - status                     #
        #********************************#
        if GPIO.input(Finger_WAKE_Pin) == 1:   
            # print("Finger Detect!")
            time.sleep(0.01)
            if GPIO.input(Finger_WAKE_Pin) == 1: 
                GPIO.output(Finger_RST_Pin, GPIO.HIGH)   
                time.sleep(0.25)	   
                r = self.VerifyUser()
                GPIO.output(Finger_RST_Pin, GPIO.LOW)
                return r     
            # checking ACK_TIMEOUT, ACK_FAIL, ACK_SUCCESS, ACK_NO_USER                 
#***************************************************************************
# @brief    Clear Module
#***************************************************************************/
    def ClearModule(self):
        if ser != None:
            ser.close()               
        GPIO.cleanup()    
#***************************************************************************
# @brief    Clear Module
#***************************************************************************/      
    def ModuleReset(self):
        self.powerDisable()
        time.sleep(0.25) 
        self.powerEnable()
        time.sleep(0.25) 
  
                
                