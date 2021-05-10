#!/usr/bin/python3
import sys
import requests
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from PyQt5 import QtCore, QtMultimedia
from finger_sensor import SZM219
import time
from datetime import datetime


#RESPONSE CODE FROM READER
ACK_SUCCESS           = 0x00
ACK_FAIL              = 0x01
ACK_FULL              = 0x04
ACK_NO_USER           = 0x05
ACK_TIMEOUT           = 0x08
ACK_GO_OUT            = 0x0F 
ACK_USER_OCCUPIED     = 0x06
ACK_FINGER_OCCUPIED   = 0x07
NO_DB                 = 0x68


#ANIMATION ICON FILE
GIF = 'ArrowDown.gif' 
AccessGranted = 'Pass.gif'
AccessDenied = 'Fail.gif'
Scan = 'Scanner.gif'

#DIALOG CODE
SUCCESS = 1
DEFAULT = 2
DANGER  = 3

#GLOBAL VARIABLE FROM READER
isActive = True
DATA_ID = 0
USER_CATEGORY = 0
READER_ID = 0
USER_COUNT = 0
READER_TIMEOUT = 0
NORMAL = 1
GUEST  = 2
ADMIN  = 3

#LIBRARY CALL
szm219 = SZM219()

#LIST OF API
# PING = 'http://localhost:3000'
USERS_API = 'http://localhost:3000/users/'
ATTENDANCES_API = 'http://localhost:3000/attendances/'

def getAllUsers(URL):
    try:       
        r = requests.get(URL)
        if r.status_code == 200:
            data = json.loads(r.content)
            return data
    except:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Unable to retrive Users")
        msg.setWindowTitle("Warning !")
        msg.setStandardButtons(QMessageBox.Ok)
        return '404'
        
def totalUsersInDB(URL):
    count = 0
    try:       
        r = requests.get(URL)
        if r.status_code == 200:
            data = json.loads(r.content)
            if len(data) != 0 :
                for i in range(0,len(data)):
                    if data[i]['reader_id'] == READER_ID:          
                        count += 1
                
                return count  
            else: 
                return count 
        else:
            return count 
    except:
        return count

def deleteUsers(URL):
    result = {'status': ACK_FAIL}
    try:
        r = requests.delete(URL)
        if r.status_code == 200:
            result = {'status': ACK_SUCCESS}
            return result
        else:
            return result
    except:
        return result        

def AttendancesAdd(reader_id,data_id,user_category,name,register_type):
    result = {'status': ACK_FAIL, 'data_id': data_id}
    if register_type == 1:
        register = 'IN'
    elif register_type == 0:
        register = 'OUT'
    data = {'reader_id' : reader_id,
                 'data_id': int(data_id),
                 'name' : name,
                 'user_category' :user_category,
                 'register_type' :register}
    try:
        r = requests.post(ATTENDANCES_API, data = data)
        if r.status_code == 201:
            result = {'status': ACK_SUCCESS, 'data_id': data_id}
            return result
        else:
            return result
    except:  
        return result
    
def getAllAttendances(URL):
    try:
        r = requests.get(URL)
        if r.status_code == 200:
            data = json.loads(r.content)
            return data
    except:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)

        msg.setText("Unable to retrive Attendance log")
        msg.setWindowTitle("Warning !")
        msg.setStandardButtons(QMessageBox.Ok)
        print("getAllAttendances : Failed" )
        return '404'

def deleteAttendances(URL):
    result = {'status': ACK_FAIL}
    try:
        r = requests.delete(URL)
        if r.status_code == 200:
            result = {'status': ACK_SUCCESS}
            return result
    except:
        return result         

def verifyDataIdToDB(data_id):
    result = {'name': 'Unknown','status': ACK_FAIL}
    try:
        r = requests.get(USERS_API)
        if r.status_code == 200:
            data = json.loads(r.content)
            if len(data) != 0 :
                for i in range(0,len(data)):
                    if data[i]['reader_id'] == READER_ID and data[i]['data_id'] == data_id:            
                        result = {'name': data[i]['name'],'status': ACK_SUCCESS}    
                        return result   
                return result                     
            else:
                return result 
        else:
            return result 
    except:   
        result = {'name': 'Unknown','status': NO_DB}
        return result 

def registerNewUsers(reader_id, data_id,user_category,name,eigent):
    result = {'status': ACK_FAIL}
    # print('data id', data_id)
    data = {'reader_id' : int(reader_id),
             'data_id' : int(data_id),
             'user_category' : user_category+1,
             'name' : name,
             'eigen_values' : eigent}
    try:
        r = requests.post(USERS_API, data = data)
        if r.status_code == 201:   
            result = {'status': ACK_SUCCESS}        
            return result
        else: 
            return result
    except: 
        return result
def updateCurrentUsers(id,reader_id, data_id,user_category,name,eigent): 
    result = {'status': ACK_FAIL}
    data = {'reader_id' : int(reader_id),
         'data_id' : int(data_id),
         'user_category' : user_category+1,
         'name' : name,
         'eigen_values' : eigent}
    try:
        r = requests.put(USERS_API + str(id), data = data)
        if r.status_code == 200:
            result = {'status': ACK_SUCCESS}
            return result
        else:
            return result
    except:
        return result        
    
def GetUserCountInReader():
    r = szm219.GetUserCount()
    if r[2] == ACK_SUCCESS:
        user_count = []
        user_count.append(r[0])
        user_count.append(r[1])
        return szm219.BytesToInt(user_count)
    return 0
        
def GetReaderID():
    r = szm219.GetSerialNumber()
    if r[3] == ACK_SUCCESS:
        SN = []
        SN.append(r[0])
        SN.append(r[1])
        SN.append(r[2])
        return szm219.BytesToInt(SN)

def SetReaderID(id):
    global READER_ID
    r = szm219.SetSerialNumber(id)
    return r
        
def queryUserInReader(id):
    r = szm219.Query_Permission(id)
    return r
        
class restore(QWidget):
    def __init__(self):
        super().__init__()
        global USERS_API
        global READER_ID
        self.editDataDB = QLineEdit()
        self.editDataReader = QLineEdit()
        
        formLayout = QFormLayout()
        formLayout.addRow("Total data on DB:", self.editDataDB)
        formLayout.addRow("Total data on reader:", self.editDataReader)
        
        self.tableDataReader = QTableWidget(self)
        self.tableDataReader.setColumnCount(3)
        self.tableDataReader.setColumnWidth(0, 60) #data_id
        self.tableDataReader.setColumnWidth(1, 60) #category
        self.tableDataReader.setColumnWidth(2, 300)#Owner
        
        #set table header
        self.tableDataReader.setHorizontalHeaderLabels(['Data Id','Category', 'Owner'])
        
        self.btnClose = QPushButton('Close')
        self.btnRestore = QPushButton('Restore')
        self.btnRefresh = QPushButton('Refresh')
        
        self.btnRestore.clicked.connect(self.downloadEigen)
        self.btnRefresh.clicked.connect(self.refreshUsersRow)
                
        restoreLayout = QVBoxLayout()
        btnRestoreLayout = QHBoxLayout()
        btnRestoreLayout.addStretch(1)
        btnRestoreLayout.addWidget(self.btnRefresh)
        btnRestoreLayout.addWidget(self.btnRestore)
        btnRestoreLayout.addWidget(self.btnClose)       
        
        restoreLayout.addLayout(formLayout)
        restoreLayout.addWidget(self.tableDataReader)
        restoreLayout.addLayout(btnRestoreLayout)
        
        self.setLayout(restoreLayout)
            
        self.refreshUsersRow()
        
    def downloadEigen(self):
        self.btnRestore.setEnabled(False)
        szm219.ModuleReset()
        if self.totalReaderData != 0:
            szm219.ClearAllUser()
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.restoringTask)
        self.worker.done.connect(self.thread.quit)
        self.worker.done.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # self.worker.progress.connect(self.addDataOnTable)
        self.worker.done.connect(self.finishRestore)
        self.thread.start()
  
    def finishRestore(self):
        self.refreshUsersRow()
        szm219.powerDisable()  
        
    def getDataOnReader(self):
        szm219.ModuleReset()
        loopCount = GetUserCountInReader()
        id = 1
        category = ''
        while loopCount > 0:
            r = queryUserInReader(id)
            Owner = 'Unknown'
            if r[1] ==  ACK_SUCCESS:
                re = verifyDataIdToDB(id)
                if re['status'] == ACK_SUCCESS:
                    Owner = re['name']
                    if r[0] == NORMAL: category = 'Normal'
                    if r[0] == GUEST: category = 'Guest'
                    if r[0] == ADMIN: category = 'Admin'
                row_add = [id,category,Owner]
                self.addDataOnTable(row_add)
                loopCount -= 1
                id += 1
            elif r[1] == ACK_NO_USER:
                id += 1
            else:
                break
        szm219.powerDisable()


    def addDataOnTable(self, row_data):
        row = self.tableDataReader.rowCount()
        self.tableDataReader.setRowCount(row+1)
        col = 0
        for item in row_data:
            cell = QTableWidgetItem(str(item))
            cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tableDataReader.setItem(row, col, cell)
            col += 1    
            
    def refreshUsersRow(self):
        szm219.ModuleReset()
        self.totalReaderData = GetUserCountInReader()
        szm219.powerDisable()
    
        self.totalDbData = totalUsersInDB(USERS_API)
        self.editDataReader.setText(str(self.totalReaderData))
        self.editDataDB.setText(str(self.totalDbData))
        
        if self.totalReaderData == self.totalDbData:
            self.btnRestore.setEnabled(False)
            
        while (self.tableDataReader.rowCount() > 0):
            self.tableDataReader.removeRow(0)  
        self.getDataOnReader()            
            
    def removeTableUsersRow(self):
        row = self.tableUsers.currentRow()    
        self.tableDataReader.removeRow(row) 
        
class ApplicationManagement(QWidget):
    def __init__(self):
        super().__init__()
        global USER_COUNT
        global READER_ID
        self.setWindowTitle('Application Management')  
        self.setWindowIcon(QIcon('setting.png'))
        
        # Initialize tab
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = restore()
        self.tabs.resize(300,200)
          
        # Add tabs
        self.tabs.addTab(self.tab1,"Users")
        self.tabs.addTab(self.tab2,"Attendance Logs")
        self.tabs.addTab(self.tab3,"Settings")
        self.tabs.addTab(self.tab4,"Restore")
        
        self.tab4.btnClose.clicked.connect(self.close)
        
        #********************************************************#
        #                    TAB Users                           #
        #********************************************************#  
        # create Users Data button
        self.btnAdd = QPushButton("Add",self)
        self.btnClose = QPushButton("Close",self)
        self.btnRefresh = QPushButton("Refresh",self)
        self.btnSearchUsers = QPushButton("Search",self)
        
        self.editUsersSearch = QLineEdit()
        
        # action button
        self.btnClose.clicked.connect(self.quit)
        self.btnAdd.clicked.connect(self.addUser)
        self.btnRefresh.clicked.connect(self.refreshUsersRow)  
        self.btnSearchUsers.clicked.connect(self.searchUsers)        
        
        # add table
        self.tableUsers = QTableWidget(self)
        self.tableUsers.setColumnCount(9)
        self.tableUsers.setColumnWidth(0, 40) #id
        self.tableUsers.setColumnWidth(1, 60) #reader_id
        self.tableUsers.setColumnWidth(2, 60) #data_id
        self.tableUsers.setColumnWidth(3, 60) #category
        self.tableUsers.setColumnWidth(4, 300)#name
        self.tableUsers.setColumnWidth(5, 300)#eigen_value
        self.tableUsers.setColumnWidth(6, 200)#register_date
        
        #set table header
        self.tableUsers.setHorizontalHeaderLabels(['Id','Reader Id', 'Data Id','Category','Name','Eigen Values','Register Date','',''])
       
        # create layout
        tableUsersLayout = QVBoxLayout()
        buttonUsersLayout = QHBoxLayout()
        usersSearchLayout = QHBoxLayout()
        buttonUsersLayout.addStretch(1)
        
        usersSearchLayout.addWidget(self.btnSearchUsers)
        usersSearchLayout.addWidget(self.editUsersSearch)
        buttonUsersLayout.addWidget(self.btnRefresh)
        buttonUsersLayout.addWidget(self.btnAdd)
        buttonUsersLayout.addWidget(self.btnClose)
        
        tableUsersLayout.addLayout(usersSearchLayout)
        tableUsersLayout.addWidget(self.tableUsers)
        tableUsersLayout.addLayout(buttonUsersLayout)
       
        self.tab1.setLayout(tableUsersLayout)
        
        #********************************************************#
        #                    TAB Attendances                     #
        #********************************************************#      
        # add table all attendaces
        self.tableAttendaces = QTableWidget(self)
        self.tableAttendaces.setColumnCount(8)
        self.tableAttendaces.setColumnWidth(0, 40) #id
        self.tableAttendaces.setColumnWidth(1, 60) #reader_id
        self.tableAttendaces.setColumnWidth(2, 60) #data_id
        self.tableAttendaces.setColumnWidth(3, 60) #Category
        self.tableAttendaces.setColumnWidth(4, 350)#name
        self.tableAttendaces.setColumnWidth(5, 60) #Register_type
        self.tableAttendaces.setColumnWidth(6, 300)#register_date
        
         #set table header
        self.tableAttendaces.setHorizontalHeaderLabels(['Id','Reader Id', 'Data Id','Category','Name','IN / OUT','Register Date',''])
        
        # create button
        self.btnClose1 = QPushButton("Close",self)
        self.btnRefresh1 = QPushButton("Refresh",self)
        self.btnSearchAttendances = QPushButton("Search",self)
        
        # create edit
        self.editAttendancesSearch = QLineEdit()
        
        # create signal
        self.btnClose1.clicked.connect(self.quit)
        self.btnRefresh1.clicked.connect(self.refreshAttendancesRows)
        self.btnSearchAttendances.clicked.connect(self.searchAttendances)
        
        #create layout
        attendancesSearchLayout = QHBoxLayout()
        tableAttendaceslayout = QVBoxLayout()
        butonAttendaceslayout = QHBoxLayout()
        butonAttendaceslayout.addStretch(1)
        
        attendancesSearchLayout.addWidget(self.btnSearchAttendances)
        attendancesSearchLayout.addWidget(self.editAttendancesSearch)
        
        tableAttendaceslayout.addLayout(attendancesSearchLayout)
        tableAttendaceslayout.addWidget(self.tableAttendaces)
        butonAttendaceslayout.addWidget(self.btnRefresh1)
        butonAttendaceslayout.addWidget(self.btnClose1)
        tableAttendaceslayout.addLayout(butonAttendaceslayout)
        
        self.tab2.setLayout(tableAttendaceslayout)
        
        #********************************************************#
        #                    TAB Settings                        #
        #********************************************************#        
        # Reader       
        # create lable
        self.lblReaderID      = QLabel('Reader ID :')
        self.lblSourceUsers    = QLabel('Source Users :')
        self.lblSourceAttendances = QLabel('Source Attendances :')
        
        # create line text
        self.editReaderId = QLineEdit(str(READER_ID))
        self.editSourceUsers = QLineEdit(settings.value('UsersSource'))
        self.editSourceAttendances = QLineEdit(settings.value('AttendanceSource'))

        # set all input readonly
        self.editReaderId.setReadOnly(True)
        self.editSourceUsers.setReadOnly(True)
        self.editSourceAttendances.setReadOnly(True)
        
        # create validator
        self.onlyInt = QIntValidator()
        self.editReaderId.setValidator(self.onlyInt)
        self.editReaderId.setToolTip('Please insert : 0 ~ 16777215') 
        
        # create button
        self.btnSetReaderID = QPushButton('Change')
        self.btnSetUsersSource = QPushButton('Change')
        self.btnSetAttendancesSource = QPushButton('Change')

        # connect signal button
        self.btnSetReaderID.clicked.connect(self.toSetReaderID)
        self.btnSetUsersSource.clicked.connect(self.changeUsersSource)
        self.btnSetAttendancesSource.clicked.connect(self.changeAttendancesSource)
        
        # create Reader layout 
        self.ReaderLayout = QGridLayout()
        self.ReaderLayout.addWidget(self.lblReaderID,0,0)
        self.ReaderLayout.addWidget(self.editReaderId,0,1)
        self.ReaderLayout.addWidget(self.btnSetReaderID,0,2)
        
        self.ReaderLayout.addWidget(self.lblSourceUsers,1,0)
        self.ReaderLayout.addWidget(self.editSourceUsers,1,1)
        self.ReaderLayout.addWidget(self.btnSetUsersSource,1,2)
        
        self.ReaderLayout.addWidget(self.lblSourceAttendances,2,0)
        self.ReaderLayout.addWidget(self.editSourceAttendances,2,1)
        self.ReaderLayout.addWidget(self.btnSetAttendancesSource,2,2)
   
        
        #create group
        groupReader = QGroupBox("Reader")
        groupReader.setLayout(self.ReaderLayout)
        
        # Main Screen
        # Create Label
        self.lblTitle = QLabel('Title :')
        self.lblTitleColor = QLabel('Title Color :')
        self.lblTextColor = QLabel('Text Color :')
        self.lblBackgroundImage = QLabel('Background Image :')
        self.lblTimeFomat = QLabel('Time Format :')
        self.lblDateFormat = QLabel('Date Format :')
        
        # create line edit
        self.editTitle = QLineEdit(settings.value('Title'))
        self.editTitleColor = QLineEdit(settings.value('TitleColor'))
        self.editTextColor = QLineEdit(settings.value('TextColor'))
        self.editBackgoundImage = QLineEdit(settings.value('BackgroundImage'))
        self.cmdTimeFormat = QComboBox()
        self.cmdTimeFormat.addItems(['h:mm AP','h:mm:ss AP','hh:mm:ss AP','H:mm','HH:mm','HH:mm:ss'])
        self.cmdTimeFormat.setCurrentText(settings.value('TimeFormat'))
        self.cmdDateFormat = QComboBox()
        self.cmdDateFormat.addItems(['dd-MM-yyyy','dd.MM.yyyy','dd MMM yyyy','ddd, dd MMMM yyyy','dddd, dd MMMM yyyy'])
        self.cmdDateFormat.setCurrentText(settings.value('DateFormat'))
       
        self.editTitle.setReadOnly(True)
        self.editTitleColor.setReadOnly(True)
        self.editTextColor.setReadOnly(True)
        self.editBackgoundImage.setReadOnly(True)
        self.cmdTimeFormat.setEnabled(False)
        self.cmdDateFormat.setEnabled(False)
        
        # create button
        self.btnTitle = QPushButton('Change')
        self.btnTitleColor = QPushButton('Change')
        self.btnTextColor = QPushButton('Change')
        self.btnBackgroundImage = QPushButton('Change')
        self.btnTimeFormat = QPushButton('Change')
        self.btnDateFormat = QPushButton('Change')
        
        # connect signal button
        self.btnTitle.clicked.connect(self.changeTitle)
        self.btnTitleColor.clicked.connect(self.changeTitleColor)
        self.btnTextColor.clicked.connect(self.changeTextColor)
        self.btnBackgroundImage.clicked.connect(self.changeBackgroundImage)
        self.btnTimeFormat.clicked.connect(self.changeTimeFormat)
        self.btnDateFormat.clicked.connect(self.changeDateFormat)
        
        # create main screen layout
        mainScreenLayout = QGridLayout()
        mainScreenLayout.addWidget(self.lblTitle,0,0)
        mainScreenLayout.addWidget(self.editTitle,0,1)
        mainScreenLayout.addWidget(self.btnTitle,0,2)
        mainScreenLayout.addWidget(self.lblTitleColor,1,0)
        mainScreenLayout.addWidget(self.editTitleColor,1,1)
        mainScreenLayout.addWidget(self.btnTitleColor,1,2)
        mainScreenLayout.addWidget(self.lblTextColor,2,0)
        mainScreenLayout.addWidget(self.editTextColor,2,1)
        mainScreenLayout.addWidget(self.btnTextColor,2,2)
        mainScreenLayout.addWidget(self.lblBackgroundImage,3,0)
        mainScreenLayout.addWidget(self.editBackgoundImage,3,1)
        mainScreenLayout.addWidget(self.btnBackgroundImage,3,2)
        mainScreenLayout.addWidget(self.lblTimeFomat,4,0)
        mainScreenLayout.addWidget(self.cmdTimeFormat,4,1)
        mainScreenLayout.addWidget(self.btnTimeFormat,4,2)
        mainScreenLayout.addWidget(self.lblDateFormat,5,0)
        mainScreenLayout.addWidget(self.cmdDateFormat,5,1)
        mainScreenLayout.addWidget(self.btnDateFormat,5,2)
        
        groupData = QGroupBox("Main Screen")
        groupData.setLayout(mainScreenLayout)
        
        self.btnClose2 = QPushButton('Close')
        self.btnApply = QPushButton('Apply')
        
        self.btnClose2.clicked.connect(self.quit)
        self.btnApply.clicked.connect(self.saveAllsetting)
               
        settingButtonLayout = QHBoxLayout()
        settingButtonLayout.addStretch(1)
        settingButtonLayout.addWidget(self.btnApply)
        settingButtonLayout.addWidget(self.btnClose2)
        
        allSettingLayout = QVBoxLayout()
        allSettingLayout.addWidget(groupReader)
        allSettingLayout.addWidget(groupData)
        allSettingLayout.addStretch(1)
        
        SettingLayout = QVBoxLayout()
        SettingLayout.addLayout(allSettingLayout)
        SettingLayout.addLayout(settingButtonLayout)
        
        self.tab3.setLayout(SettingLayout)
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        # self.setGeometry(300,400,500,400)
        
    def changeUsersSource(self):
        if self.btnSetUsersSource.text() == 'Change':
            self.editSourceUsers.setReadOnly(False)
            self.btnSetUsersSource.setText('Set')
        else:
            self.editSourceUsers.setReadOnly(True)
            self.btnSetUsersSource.setText('Change')
            
    def changeAttendancesSource(self):
        if self.btnSetAttendancesSource.text() == 'Change':
            self.editSourceAttendances.setReadOnly(False)
            self.btnSetAttendancesSource.setText('Set')
        else:
            self.editSourceAttendances.setReadOnly(True)
            self.btnSetAttendancesSource.setText('Change')
    
    def changeTitle(self):
        if self.btnTitle.text() == 'Change':
            self.editTitle.setReadOnly(False)
            self.btnTitle.setText('Set')
        else:
            self.editTitle.setReadOnly(True)
            self.btnTitle.setText('Change')
            
    def changeTitleColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.editTitleColor.setText(color.name())
            
    def changeTextColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.editTextColor.setText(color.name())
            
    def changeBackgroundImage(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Image (*.jpg)", options=options)
        if fileName:
            self.editBackgoundImage.setText(fileName)
    
    def changeTimeFormat(self):
        if self.btnTimeFormat.text() == 'Change':
            self.cmdTimeFormat.setEnabled(True)
            self.btnTimeFormat.setText('Set')
        else:
            self.btnTimeFormat.setText('Change')
            self.cmdTimeFormat.setEnabled(False)

    def changeDateFormat(self):
        if self.btnDateFormat.text() == 'Change':
            self.cmdDateFormat.setEnabled(True)
            self.btnDateFormat.setText('Set')
        else:
            self.btnDateFormat.setText('Change')
            self.cmdDateFormat.setEnabled(False)
    
    def toSetReaderID(self):
        global READER_ID
        if self.btnSetReaderID.text() == 'Change':
            reply = QMessageBox.warning(self,'Question',
                                        "This change may make all current registered users anonymous to the database, Are you sure to continue?", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.editReaderId.setReadOnly(False)
                self.btnSetReaderID.setText('Set')
        else:
            if int(self.editReaderId.text()) >= 0 and  int(self.editReaderId.text()) <=  16777215:
                szm219.ModuleReset()
                r = SetReaderID(int(self.editReaderId.text()))
                if r == ACK_SUCCESS:
                    READER_ID = int(self.editReaderId.text())
                    self.editReaderId.setReadOnly(True)
                    reply = QMessageBox.information(self, 'Info !',"Reader id was successfully changed", QMessageBox.Ok )
                else:
                    reply = QMessageBox.warning(self, 'Warning !',"Reader id fail to changed", QMessageBox.Ok )
                szm219.powerDisable()
                self.btnSetReaderID.setText('Change')
            else:
                reply = QMessageBox.warning(self, 'Warning !',"Please insert 0 - 16777215", QMessageBox.Ok )
                    
            
    def searchUsers(self):
        if len(self.editUsersSearch.text()) == 0:
            self.refreshUsersRow()
        else:
            for row in range(self.tableUsers.rowCount()):
                self.tableUsers.setRowHidden(row, True)
            items = self.tableUsers.findItems(self.editUsersSearch.text(), Qt.MatchContains)
            if items:  # we have found something
                for item in items:  # take the first
                    self.tableUsers.setRowHidden(item.row(), False)

    def queryUsers(self):
        data = getAllUsers(USERS_API)
        if len(data) > 0 and data !='404':
            for i in range(0,len(data)):
                if data[i]['user_category'] == '1': category = 'Normal'
                if data[i]['user_category'] == '2': category = 'Guest'
                if data[i]['user_category'] == '3': category = 'Admin'
                row_add = [ data[i]['id'],
                            data[i]['reader_id'], 
                            data[i]['data_id'],
                            category, 
                            data[i]['name'], 
                            data[i]['eigen_values'],
                            data[i]['register_date']]
                            
                self.addTableUsersRow(row_add)
            
        
    def refreshUsersRow(self):
        while (self.tableUsers.rowCount() > 0):
            self.tableUsers.removeRow(0)
        self.queryUsers()
    def addUser(self):
        global READER_ID
        add.display(0,'',str(READER_ID),'0','Normal','','')
    def editTableRow(self):
        row = self.tableUsers.currentRow()
        add.display(1,self.tableUsers.item(row,0).text(), 
                             self.tableUsers.item(row,1).text(), 
                             self.tableUsers.item(row,2).text(), 
                             self.tableUsers.item(row,3).text(), 
                             self.tableUsers.item(row,4).text(),
                             self.tableUsers.item(row,5).text())      
    def removeTableUsersRow(self):
        row = self.tableUsers.currentRow()
        id = int(self.tableUsers.item(row,0).text())
        user_id = int(self.tableUsers.item(row,2).text())
        reply = QMessageBox.question(self,'Question',
                                    "Are you sure to delete " + "<html><b>" + self.tableUsers.item(row,4).text() + "</b</html> ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            response = deleteUsers(USERS_API + str(id))
            if response['status'] == ACK_SUCCESS:
                self.tableUsers.removeRow(row)
                szm219.ModuleReset()
                r = szm219.DeleteUser(user_id)
                if r != ACK_SUCCESS:
                    print('remove users : fail to remove from reader')
                szm219.powerDisable()
            else:
                popup.display(AccessDenied,"Failed !", "Unable to delete users, plaese check network connection",DANGER,5)
                print('Fail to remove user id :' + str(id) + ' from db') 
        else:
            print("Cancel delete :", id) 
        
    def addTableUsersRow(self,row_data):
        row = self.tableUsers.rowCount()
        self.tableUsers.setRowCount(row+1)
        btnEdit = QPushButton("Edit")
        btnDelete = QPushButton("Delete")
        btnDelete.clicked.connect(self.removeTableUsersRow)
        btnEdit.clicked.connect(self.editTableRow)
        col = 0
        for item in row_data:
            cell = QTableWidgetItem(str(item))
            cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tableUsers.setItem(row, col, cell)
            self.tableUsers.setCellWidget(row,7,btnEdit)
            self.tableUsers.setCellWidget(row,8,btnDelete)
            col += 1
    def queryAttendances(self):
        data = getAllAttendances(ATTENDANCES_API)
        if len(data) > 0 and  data != '404':
            for i in range(0,len(data)):
                if data[i]['user_category'] == '1': category = 'Normal'
                if data[i]['user_category'] == '2': category = 'Guest'
                if data[i]['user_category'] == '3': category = 'Admin'
                row_add = [ data[i]['id'],
                            data[i]['reader_id'], 
                            data[i]['data_id'],
                            category, 
                            data[i]['name'], 
                            data[i]['register_type'],
                            data[i]['register_date']]
                self.addTableAttendanceRow(row_add)
                    
    def addTableAttendanceRow(self,row_data):
        row = self.tableAttendaces.rowCount()
        self.tableAttendaces.setRowCount(row+1)
        btnDelete = QPushButton("Delete")
        btnDelete.clicked.connect(self.removeTableAttendancesRow)
        col = 0
        for item in row_data:
            cell = QTableWidgetItem(str(item))
            cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tableAttendaces.setItem(row, col, cell)
            self.tableAttendaces.setCellWidget(row,7,btnDelete)
            col += 1
    def removeTableAttendancesRow(self):
        row = self.tableAttendaces.currentRow()
        id = int(self.tableAttendaces.item(row,0).text())
        reply = QMessageBox.question(self,'Question',
                                    "Are you sure to delete " + "<html><b>" + self.tableAttendaces.item(row,4).text() + "</b</html> ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            r = deleteAttendances(ATTENDANCES_API + str(id))
            if r['status'] == ACK_SUCCESS:
                self.tableAttendaces.removeRow(row)
            else:
                popup.display(AccessDenied,"Failed !", "Unable to delete atendance, plaese check network connection",DANGER,5)
                
    def refreshAttendancesRows(self):
        while (self.tableAttendaces.rowCount() > 0):
            self.tableAttendaces.removeRow(0)
        self.queryAttendances()
    def searchAttendances(self):
        if len(self.editAttendancesSearch.text()) == 0:
            self.refreshAttendancesRows()
        else:
            for row in range(self.tableAttendaces.rowCount()):
                self.tableAttendaces.setRowHidden(row, True)
            items = self.tableAttendaces.findItems(self.editAttendancesSearch.text(), Qt.MatchContains)
            if items:  # we have found something
                for item in items:  # take the first
                    self.tableAttendaces.setRowHidden(item.row(), False)
    def quit(self):
        menu.close()
    def saveAllsetting(self):
        settings.setValue('UsersSource',self.editSourceUsers.text())
        settings.setValue('AttendanceSource',self.editSourceAttendances.text())
        settings.setValue('Title',self.editTitle.text())
        settings.setValue('TitleColor',self.editTitleColor.text())
        settings.setValue('TextColor',self.editTextColor.text())
        settings.setValue('BackgroundImage',self.editBackgoundImage.text())
        settings.setValue('TimeFormat',self.cmdTimeFormat.currentText())
        settings.setValue('DateFormat',self.cmdDateFormat.currentText())
        main.ScreenChangeApply()
        
    def showEvent(self, event):
        global isActive
        isActive = False
        self.refreshUsersRow()
        self.refreshAttendancesRows()
        event.accept()
    def closeEvent(self, event):
        global isActive
        isActive = True
        if self.btnSetUsersSource.text() == 'Set' or self.btnSetAttendancesSource.text() == 'Set' or self.btnTitle.text() == 'Set' or self.btnTimeFormat.text() == 'Set' or self.btnDateFormat.text() == 'Set':
            reply = QMessageBox.warning(self,'Warning',"Please ensure all settings value was set",QMessageBox.Ok)
            event.ignore()
        else: 
            event.accept()
            
class Worker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(list)
    done     = pyqtSignal()

    def addUserTask(self):
        """running task."""
        data = []
        szm219.ModuleReset()
        data = szm219.addUser(add.cmbCategory.currentIndex()+1) 
        self.finished.emit(data)          
    def scanningTaks(self):
        data = []  
        data = szm219.VerifyUser()
        self.finished.emit(data)
    def restoringTask(self):
        data = getAllUsers(USERS_API)
        if len(data) != 0 and data != '404':
            for i in range(len(data)):
                if data[i]['reader_id'] == READER_ID:
                    data_id = data[i]['data_id']
                    permission = data[i]['user_category']
                    eigen = data[i]['eigen_values']
                    eigen_value = szm219.HexStringToByteArray(eigen)
                    szm219.SetEigenById(data_id,int(permission),eigen_value)
        self.done.emit()            
        
class AddData(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Window | Qt.WindowStaysOnTopHint)
        self.isEdit = 0
        self.id = 0
        self.reader_id = 0
        self.data_id = 0
        self.name = ''
        self.eigen = ''
        
        self.category = 0
        self.isScan = 1
        self.isSaved = 0
        
        self.editReaderId = QLineEdit()
        self.editDataId = QLineEdit()
        self.cmbCategory = QComboBox()
        self.cmbCategory.addItems(['Normal','Guest','Admin'])
        self.editName = QLineEdit(self.name)
        self.editEigen = QTextEdit()
        self.editReaderId.setReadOnly(True)
        self.editDataId.setReadOnly(True)
        self.editEigen.setReadOnly(True)
 
        # Create a form layout and add widgets
        dlgLayout = QVBoxLayout()
        
        formLayout = QFormLayout()
        formLayout.addRow("Reader Id:", self.editReaderId)
        formLayout.addRow("Data Id:", self.editDataId)
        formLayout.addRow("Category:", self.cmbCategory)
        formLayout.addRow("Name:*", self.editName)
        formLayout.addRow("Eigen:", self.editEigen)
        
        self.btnCancel = QPushButton("Close",self)
        self.btnSaveOrScan = QPushButton("Start scan",self)
        
        self.btnCancel.clicked.connect(self.cancel)
        self.btnSaveOrScan.clicked.connect(self.save)
        
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnCancel)
        btnLayout.addWidget(self.btnSaveOrScan)
        
        # Set the layout on the dialog
        dlgLayout.addLayout(formLayout)
        dlgLayout.addLayout(btnLayout)
        self.setLayout(dlgLayout)
    
    def display(self,isEdit,id,reader_id,data_id,category,name,eigen):   
        self.isEdit = isEdit
        self.id = id
        self.reader_id = reader_id
        self.data_id = data_id
        self.name = name
        self.eigen = eigen
        
        
        if category == 'Normal': self.category = 0
        if category == 'Guest': self.category = 1
        if category == 'Admin': self.category = 2
        
        self.editReaderId.setText(self.reader_id)
        self.editDataId.setText(self.data_id)
        self.cmbCategory.setCurrentIndex(self.category)
        self.editName.setText(self.name)
        self.editEigen.setText(self.eigen)
        
        if isEdit == 0:
            self.btnSaveOrScan.setText('Start scan')
        elif isEdit == 1:
            self.editReaderId.setReadOnly(True)
            self.cmbCategory.setEnabled(False)
            self.btnSaveOrScan.setText('Save')
       
        self.setGeometry(490, 220, 300, 200)
        self.setFixedSize(300, 200)
        self.show()
    def save(self):
         #***************#
         #    add data   #
         #***************#
        if self.isEdit == 0: # add 
            if self.btnSaveOrScan.text() == 'Start scan': # scan
                self.showScanner()
            elif self.btnSaveOrScan.text() == 'Save': # save
                response = registerNewUsers(self.editReaderId.text(),self.editDataId.text(),self.cmbCategory.currentIndex(),self.editName.text(),self.editEigen.toPlainText())
                if response['status'] == ACK_SUCCESS:
                    self.isScan = 1
                    self.isSaved = 1
                    menu.refreshUsersRow()
                    self.close()
                else:
                    popup.display(AccessDenied,"Failed !", "Unable to save users, plaese check network connection",DANGER,5)
                    self.isSaved = 0  
         #****************#
         #    edit data   #
         #****************#                
        elif self.isEdit == 1:# edit
            response = updateCurrentUsers(self.id,self.editReaderId.text(),self.editDataId.text(),self.cmbCategory.currentIndex(),self.editName.text(),self.editEigen.toPlainText())
            if response['status'] == ACK_SUCCESS:
                msg = QMessageBox.information(self, 'Info',"Data has been update successfully...", QMessageBox.Ok )
                menu.refreshUsersRow()
                self.close()
            else:
                popup.display(AccessDenied,"Failed !", "Unable to update users, plaese check network connection",DANGER,5)
                self.close()
    def showScanner(self):
        id = []
        user_id = 0
        ACK_RESPONSE = 0
        data = []     
        popup.display(Scan,"Scanning...","Place your finger center to the sensor",DEFAULT,6)        
        if len(self.editName.text()) != 0:
            self.thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.addUserTask)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.finished.connect(self.completedScan)
            self.thread.start()
        else:
            reply = QMessageBox.warning(self, 'Warning !',"Name can't be empty", QMessageBox.Ok ) 
           
    def completedScan(self, data):
        # if popup.isVisible() == True:
            # popup.close()
        if data[2] == ACK_SUCCESS:
            b_data_id = []
            b_data_id.append(data[0])
            b_data_id.append(data[1])
            data_id = szm219.BytesToInt(b_data_id)
            self.editDataId.setText(str(data_id))
            popup.display(AccessGranted,"Success !","Now you can release your finger",SUCCESS,5)
            self.isScan = 0
            self.isSaved = 0
            self.btnSaveOrScan.setText("Save")
            szm219.ModuleReset()
            eigen = szm219.GetEigenById(data_id)
            if len(eigen) == 195:
                if eigen[194] == ACK_SUCCESS:
                    einge_values = []
                    for b in range(193):
                        einge_values.append(eigen[b])
                    eigen_value_string = szm219.ByteArrayToHexString(einge_values)
                    self.editEigen.setText(eigen_value_string)
                else:
                    print('Add users : fail get eigen value')
            else:
                print('Add users : fail len eigen not valid')
        elif data[2] == ACK_TIMEOUT:
            popup.display(AccessDenied,'Sorry !','No finger detected',DANGER,3)
        elif data[2] == ACK_FAIL:
            popup.display(AccessDenied,'Failed !','Please try agin',DANGER,3) 
        elif data[2] == ACK_FINGER_OCCUPIED:
            popup.display(AccessDenied,'Sorry !','This finger already exists',DANGER,3)
        elif data[2] == ACK_FULL:
            popup.display(AccessDenied,'Sorry !','Currently storage was fully utilize',DANGER,3)         
        szm219.powerDisable()
           
    def cancel(self):           
        self.close()
    def showEvent(self, event):
        global READER_ID
        if self.isEdit == 0:
            self.setWindowTitle("Add User")
        elif self.isEdit == 1:
            self.setWindowTitle("Edit User")
        event.accept()
    def closeEvent(self, event):
        if int(self.editDataId.text())!=0 and self.isEdit == 0 and self.isSaved == 0:
            reply = QMessageBox.question(self,'Question',"Are you sure to cancel?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.scan = 1
                szm219.ModuleReset()
                r = szm219.DeleteUser(int(self.editDataId.text()))
                if r != ACK_SUCCESS:
                    print('Add users : fail to delete users')
                szm219.powerDisable()
                event.accept()
            elif reply == QMessageBox.No:
                event.ignore()
        else:
            event.accept()
            
class Popup(QWidget):
    def __init__(self):   
        super().__init__()        
                
        self.state = SUCCESS
        self.counter = 10 
        
        self.initUI()
        self.setWindowTitle('Attendance')
        
        self.lblStatus = QLabel(self)
        self.lblStatus.setFont(QFont('Arial', 25))
        self.lblStatus.setGeometry(20,160,560,55)
        self.lblStatus.setAlignment(QtCore.Qt.AlignCenter)
        self.lblStatus.show()
        
        self.lblName= QLabel(self)
        self.lblName.setFont(QFont('Arial', 12))
        self.lblName.setGeometry(20,210,560,40)
        self.lblName.setAlignment(QtCore.Qt.AlignCenter)
        self.lblName.show()
        
        self.btnOk = QPushButton("OK",self)
        self.btnOk.setGeometry(250,310,100,50)
        self.btnOk.setFont(QFont('Arial', 15))
        self.btnOk.show()
        self.btnOk.clicked.connect(self.timeOut)
        
        self.timerAutoClose = QTimer(self)
        self.timerAutoClose.timeout.connect(self.countTimer)
        # self.timerAutoClose.start(1000)
        self.timerAutoClose.stop()
        
        
        
    def display(self,icon,title,text,state,counter):
        self.counter = counter
        self.state = state
        self.timerAutoClose.start(1000)
        # print("Popup Show")    
        
        self.gif = QMovie()
        self.gif.setFileName(icon) 
        self.lblStatus.setText(title) 
        self.lblName.setText(text)
        
        if self.state == SUCCESS:
            self.btnOk.setStyleSheet("color: white;background-color: #65be25;")
            self.btnOk.setVisible(True)
        elif self.state == DANGER:
            self.btnOk.setVisible(True)
            self.btnOk.setStyleSheet("color: white;background-color: red;")
        elif self.state == DEFAULT:
            self.btnOk.setVisible(False)
            self.btnOk.setStyleSheet("color: black;background-color: #eeeee4;")
            
        
        self.picStatus = QLabel(self)
        self.gif.setScaledSize(QSize().scaled(100, 100, Qt.IgnoreAspectRatio))
        self.picStatus.setMovie(self.gif)
        self.picStatus.setGeometry(250,40,100,100)
            
        self.btnOk.setFlat(1)
        self.btnOk.setAutoFillBackground(1) 
        self.gif.start()
        self.show()
        
    def countTimer(self):
        if self.counter > 0 :
            self.counter -= 1
        else:
            self.timeOut()
    def initUI(self):
        self.setWindowTitle('Attendance')
        self.setWindowFlags(Qt.Popup)
        self.setGeometry(340, 160, 600, 400) #center
        self.setStyleSheet("background-color: white;")
    def timeOut(self):
        self.gif.stop()
        self.close()
        
    def showEvent(self, event):
        szm219.powerEnable()
        event.accept()
    def closeEvent(self, event):
        szm219.powerDisable()
        event.accept()
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global READER_ID
        global USER_COUNT
        self.TimeFormat = 'HH:mm'
        self.DateFormat = 'dddd, dd MMMM yyyy'
        self.isIN = 1
        self.resize(1280,720)

        self.setWindowTitle('Attendance System')
        self.setWindowIcon(QIcon('main.png'))
        
        self.wallpaper = QImage()
        self.wallpaper.load("ScreenWall.jpg","jpg")
        sImage = self.wallpaper.scaled(1280, 720, Qt.KeepAspectRatio)                   
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))                        
        self.setPalette(palette)
        
        self.lblWelcome = QLabel("WELCOME TO MY COMPANY",self)
        self.lblWelcome.setFont(QFont('Nimbus Mono L', 30,QFont.Bold))
        self.lblWelcome.setGeometry(0,30,1280,50)
        self.lblWelcome.setAlignment(QtCore.Qt.AlignCenter)
        self.lblWelcome.setStyleSheet("color: white;background-color: rgba(0, 0, 255, 50)")
        self.lblWelcome.show()
        
        self.lblTime = QLabel("__:__",self)
        self.lblTime.setFont(QFont('Arial', 100))
        self.lblTime.setGeometry(0,180,1280,170)
        self.lblTime.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTime.setStyleSheet("color: white;")
        self.lblTime.show()
        
        self.lblDate = QLabel("__/__/__",self)
        self.lblDate.setFont(QFont('Arial', 20,QFont.Bold))
        self.lblDate.setGeometry(0,330,1280,50)
        self.lblDate.setAlignment(QtCore.Qt.AlignCenter)
        self.lblDate.setStyleSheet("color: white;")
        self.lblDate.show()

        self.lblInfo = QLabel("Checking Fingerprint reader",self)
        self.lblInfo.setFont(QFont('Arial', 20,QFont.Bold))
        self.lblInfo.setGeometry(0,410,1280,100)
        self.lblInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblInfo.setStyleSheet("color: white;")
        self.lblInfo.show()

        self.btnIN = QPushButton('IN',self)
        self.btnIN.setGeometry(110,530,100,100)
        self.btnIN.setFont(QFont('Arial', 15,QFont.Bold))
        self.btnIN.show()
        self.btnIN.clicked.connect(self.ClockIn)

        self.btnOUT = QPushButton('OUT',self)
        self.btnOUT.setFont(QFont('Times', 15,QFont.Bold))
        self.btnOUT.setGeometry(1070,530,100,100)
        self.btnOUT.show()
        self.btnOUT.clicked.connect(self.ClockOut)
        
        self.Arrow = QLabel(self)
        gif = QMovie(GIF)
        gif.setScaledSize(QSize().scaled(100, 100, Qt.KeepAspectRatio))
        self.Arrow.setMovie(gif)
        self.Arrow.setGeometry(110,430,100,100)
        gif.start()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showTime)
        self.timer.start(1000)  
        
        szm219.ModuleReset()
        if szm219.module() == ACK_SUCCESS:
            USER_COUNT = GetUserCountInReader()
            READER_ID =  GetReaderID()
            self.lblInfo.setText("PLEASE SELECT IN OR OUT BEFORE SCAN")   
        else:
            self.lblInfo.setText("OUT OF SERVICE")
        szm219.powerDisable()
        
    def ScreenChangeApply(self):
        global USERS_API
        global ATTENDANCES_API
        USERS_API = settings.value('UsersSource')
        ATTENDANCES_API = settings.value('AttendanceSource')
        self.lblWelcome.setText(settings.value('Title')) 
        self.lblWelcome.setStyleSheet("color: " + settings.value('TitleColor') + ";background-color: rgba(0, 0, 255, 70)")
        self.lblTime.setStyleSheet("color: " + settings.value('TextColor') + ";")
        self.lblDate.setStyleSheet("color: " + settings.value('TextColor') + ";")
        self.lblInfo.setStyleSheet("color: " + settings.value('TextColor') + ";")
        self.wallpaper.load(settings.value('BackgroundImage'),"jpg")
        sImage = self.wallpaper.scaled(1280, 720, Qt.KeepAspectRatio)                   
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))                        
        self.setPalette(palette)
        self.TimeFormat = settings.value('TimeFormat')
        self.DateFormat = settings.value('DateFormat')
                
    def keyPressEvent(self, e):
        if e.key()  == Qt.Key_F1 :
            menu.showMaximized()
        if e.key() == Qt.Key_Escape:
            self.close()
    def ClockIn(self):
        self.isIN = 1
        self.Arrow.setGeometry(110,430,100,100)
    def ClockOut(self):
        self.isIN = 0
        self.Arrow.setGeometry(1070,430,100,100)
    def showTime(self): 
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        label_time = current_time.toString(self.TimeFormat)
        label_date = current_date.toString(self.DateFormat)
        self.lblTime.setText(label_time)
        self.lblDate.setText(label_date)
        self.ScanFinger()
    def ScanFinger(self):
        global USER_CATEGORY  
        global READER_ID
        global isActive
        if isActive == True:
            if szm219.isWake() == True:
                time.sleep(0.01)
                if szm219.isWake() == True:
                    szm219.powerEnable() 
                    self.timer.stop()
                    time.sleep(0.25)
                    self.thread = QThread()
                    self.worker = Worker()
                    self.worker.moveToThread(self.thread)
                    self.thread.started.connect(self.worker.scanningTaks)
                    self.worker.finished.connect(self.thread.quit)
                    self.worker.finished.connect(self.worker.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    self.worker.finished.connect(self.finishScan)
                    self.thread.start()
                    
    def finishScan(self,data):
        szm219.powerDisable()
        
        if popup.isVisible() == True: popup.close()
        if data[3] == ACK_SUCCESS:
            id = []
            id.append(data[0])
            id.append(data[1])
            user_id = szm219.BytesToInt(id)
            user_category = data[2]
            db_replay = verifyDataIdToDB(user_id)
            if db_replay['status'] == ACK_SUCCESS:
                if self.isIN == 1 : 
                    popup.display(AccessGranted,"Congrat !, Have nice day",db_replay['name'],SUCCESS,5)  
                elif self.isIN == 0 : 
                    popup.display(AccessGranted,"Bye !, see you again",db_replay['name'],SUCCESS,5)
                res = AttendancesAdd(READER_ID,user_id,user_category,db_replay['name'],self.isIN)
                if res['status'] != ACK_SUCCESS:
                    print('Fail to record attendandace data_id:' + str(res['data_id']))
            elif db_replay['status'] == NO_DB:
                popup.display(AccessDenied,"Failed !", "Currently unable to connect database, please check your network connection",DANGER,5)
            elif db_replay['status'] == ACK_FAIL:
                popup.display(AccessDenied,"Failed !", "This finger not found in database",DANGER,5)
        elif data[3] == ACK_TIMEOUT:
            popup.display(AccessDenied,"Time out !", "No finger found on sensor",DANGER,5)
        elif data[3] == ACK_NO_USER:
            popup.display(AccessDenied,"Not match !", ",Please try again...",DANGER,5)
        elif data[3] == ACK_FAIL:
            popup.display(AccessDenied,"Failed !", "Please try again",DANGER,5)
        self.timer.start()
    def closeEvent(self, event):
        szm219.ClearModule()
     
   
if __name__ == "__main__":
    app = QApplication(sys.argv)
    settings = QSettings('FingerprintApp', 'App1')
    main = MainWindow()
    menu = ApplicationManagement()
    add = AddData()
    popup = Popup()
    main.show()
    main.ScreenChangeApply()
    main.showFullScreen()
    sys.exit(app.exec_())
    
