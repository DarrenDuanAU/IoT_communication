"""
    Sample code for Multi-Threaded Server
    Python 3
    Usage: python3 TCPserver3.py localhost 12000
    coding: utf-8
    
    Author: xiaoyang Duan z3360376
"""
from datetime import datetime
from email import message
from socket import *
from threading import Thread
from collections import defaultdict
import datetime
import sys, select
import json
import os

seq_No = 1
login_block = defaultdict(datetime.datetime)

#file_name = "upload-log.txt"
#with open(file_name,"w+") as file:
    #file.write("edgeDeviceName; timestamp; fileID; dataAmount\n")

#file_name = "deletion-log.txt"
#with open(file_name,"w+") as file:
    #file.write("edgeDeviceName; timestamp; fileID; dataAmount\n")

#file_name = "edge-device-log.txt"
#with open(file_name,"w+") as file:
#    file.write("Active edge device sequence number; timestamp; edge device name; edge device IP address; edge device UDP server port number\n")


def record_etod_logbook(username, IP_add, UDPPort,timestamp):

    file_name = "edge-device-log.txt"
    with open(file_name,"r") as file:
        rows = file.readlines()
    seq_No = len(rows) + 1

    with open(file_name,"a") as file:
        file.write(str(seq_No)+"; "+str(timestamp)+"; "+username+"; "+str(IP_add[0])+"; "+str(UDPPort)+"\n")


def record_logbook(username, fileID, log_file_name,timestamp):
    file_name = str(username) +"-"+ str(fileID)+".txt"
    if os.path.exists(file_name):
        with open(file_name,"r") as file:
            num_list = file.readlines()
        dataAmount = len(num_list)

        with open(log_file_name,"a") as file:
            file.write(f"{username}; {timestamp}; {fileID}; {dataAmount}\n")
        return True
    else:
        return False

def file_generate(username,fileID,data):
    file_name = str(username) +"-"+ str(fileID)+".txt"
    with open(file_name,"w+") as file:
        file.write(data)
    return True

def file_delete(username,fileID):
    file_name = str(username) +"-"+ str(fileID)+".txt"
    if os.path.exists(file_name):
        os.remove(file_name)
        return True
    else:
        return False

def computation(username,fileID,opration):
    #SCS_check_list =[ "AVERAGE","MAX","MIN","SUM"]

    file_name =str(username) +"-"+ str(fileID)+".txt"
    if os.path.exists(file_name):
        with open(file_name,"r") as file:
            num_list = file.readlines()
        num_list = [int(x[0:-1]) for x in num_list]

        sum = 0
        count = 0
        max = num_list[0]
        min = num_list[0]

        for x in num_list:
            sum += x
            count += 1
            if x > max:
                max = x
            if x < min:
                min = x


        if opration =="SUM":
            return sum
        elif opration =="AVERAGE":
            return sum/count
        elif opration == "MAX":
            return max
        else:
            return min

    else:
        print(f"SCS: the {file_name} is not exist on server side")

def remove_etod_log(username):
    with open("edge-device-log.txt","r") as file:
        temp_data = file.readlines()
                   
    #remove the row for edge-device-log.txt which have the username
    remove_index = -1                  
    for i in range(len(temp_data)):
        if temp_data[i].split("; ")[2] == username:
            remove_index = i
    if remove_index != -1:
        del temp_data[remove_index]

        #update the seq_No of the logbook
        for i in range(remove_index,len(temp_data)):

            temp_list = temp_data[i].split("; ")
            temp_list[0] = str(i+1)

            temp_str =""
            for j in range(len(temp_list)):
                temp_str = temp_str + str(temp_list[j]) 
                if j != len(temp_list) -1:
                    temp_str = temp_str + "; "
                    
            temp_data[i] = temp_str

        file_name = "edge-device-log.txt"
        with open(file_name,"w+") as file:
            for row in temp_data:
                file.write(row)
        
        return True


# acquire server host and port from command line parameter
if len(sys.argv) != 3:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n")
    exit(0)

serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)
print("the serverAddress is: ",serverAddress)

if sys.argv[2].isnumeric() and int(sys.argv[2])>=1 and int(sys.argv[2])<=5:
    max_login_fail_times = int(sys.argv[2])
    print(f"max_login_fail_time is {max_login_fail_times}")
else:
    print("Invalid number of allowed failed consecutive attempts: number. The valid value of argument number is an integer between 1 and 5")
    sys.exit(0)

# define socket for the server side and bind address
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

"""
    Define multi-thread class for client
    This class would be used to define the instance for each connection from each client
    For example, client-1 makes a connection request to the server, the server will call
    class (ClientThread) to define a thread for client-1, and when client-2 make a connection
    request to the server, the server will call class (ClientThread) again and create a thread
    for client-2. Each client will be runing in a separate therad, which is the multi-threading
"""
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        
        print("Thread-init: ===== New connection created for: ", clientAddress, clientSocket)
        self.clientAlive = True

        self.login_faild_times = defaultdict(int)
        
        
    def run(self):
        r_message = ''
        
        s_message_dict = {}


        print("Thread-run: start run")
        while self.clientAlive:
            
            r_data = self.clientSocket.recv(1024)
            r_message = r_data.decode()
            r_message_dict = json.loads(r_message)
            print("[recv]: ",r_message_dict)

            dict.clear(s_message_dict)

            # if the message from client is empty, the client would be off-line then set the client as offline (alive=Flase)
            if r_message == '' or r_message_dict.get("act") == 'exit':
                self.clientAlive = False
                print("===== the user disconnected - ", clientAddress)
                break
            
            #the server reply to the cilent depends on the 'act' 
            if r_message_dict.get("act") == "login":
                s_message_dict["act"] = "login"

                username = r_message_dict.get("username")
                password = r_message_dict.get("password")
                UDPPort = r_message_dict.get("UDPPort")
                print(f"user_name and password are: {username} ,  {password}")

                if login_block.get(username) == None or login_block.get(username) < datetime.datetime.now():
                    self.process_login(username,password,UDPPort)
                else:
                    s_message_dict["data"] = "Blocked & Wait"

                    print(f"[send]: {s_message_dict}")
                    s_message = json.dumps(s_message_dict) 
                    self.clientSocket.send(s_message.encode())
            else:

                if r_message_dict.get("act") == "UED":
                    #print("UED data is:",r_message_dict["data"])

                    s_message_dict["act"] = "UED"
                    if r_message_dict.get("data") != None:
                        timestamp = str(datetime.datetime.now())[:19]
                        
                        #send success, if the data can be stored in file and recorded in logbook
                        if file_generate(username,r_message_dict["fileID"],r_message_dict["data"]) and record_logbook(username,r_message_dict["fileID"],"upload-log.txt",timestamp):
                            print("The file with ID of",r_message_dict["fileID"] ,"has been received, upload-log.txt file has been updated")
                            s_message_dict["data"] = "Success"
                        else:
                            s_message_dict["data"] = "Fail"

                            
                elif r_message_dict.get("act") == "SCS":
                    fileID = r_message_dict["fileID"]
                    opration = r_message_dict["opration"]

                    s_message_dict["act"] = "SCS"
                    s_message_dict["data"] = computation(username,fileID,opration)
                
                elif r_message_dict.get("act") == "DTE":
                    print(f"{username} issued DTE command, the file ID is",r_message_dict.get("fileID"))

                    s_message_dict["act"] = "DTE"
                    timestamp = str(datetime.datetime.now())[:19]
                    if record_logbook(username,r_message_dict.get("fileID"),"deletion-log.txt",timestamp) and file_delete(username,r_message_dict.get("fileID")):
                        print("delate successfully")
                        s_message_dict["data"] = "Success"
                    else:
                        print("delate failed")
                        s_message_dict["data"] = "Fail"

                elif r_message_dict.get("act") =="AED":
                    print(f"{username} issued AED command")
                    s_message_dict["act"] ="AED"

                    with open("edge-device-log.txt","r") as file:
                        temp_data = file.readlines()
               
                    temp_data = [i for i in temp_data if username != i.split("; ")[2]]
                    s_message_dict["data"] = temp_data
                    print("AED data sending to the client:",s_message_dict["data"])
                
                elif r_message_dict["act"] == "OUT":
                    print(f"{username} issued OUT command")
                    s_message_dict["act"] = "OUT"
                    if remove_etod_log(username) ==True:
                        s_message_dict["data"] = "Success"
                        
                            
                else:
                    s_message_dict["act"] ="ND"
                    s_message_dict["data"] =""



                print(f"[send]: {s_message_dict}")
                s_message = json.dumps(s_message_dict) 
                self.clientSocket.send(s_message.encode())
                print(f"returning message to {username}.....")

                if r_message_dict.get("act") == "OUT":
                    self.clientAlive = False
                    print("===== the user disconnected - ", clientAddress)
                    break
    
    """
        You can create more customized APIs here, e.g., logic for processing user authentication
        Each api can be used to handle one specific function, for example:
        def process_login(self):
            message = 'user credentials request'
            self.clientSocket.send(message.encode())
    """
    def process_login(self,username,password,UDPPort):
        
        s_message_dict = {}
        s_message_dict["act"] = "login"

        #load the credentials.txt
        with open("credentials.txt","r") as credential_file:
            credential_content = credential_file.read()

            #check the weather user_name and password matched the credential
            login_success = False
            for row in credential_content.split("\n"):
                try:
                    cre_user_name,cre_password = row.split(" ")
                except:
                    continue

                if cre_user_name == username and cre_password == password:
                    login_success = True
                    break
            
            #send "Login success" to the client or count the failed_time 
            #block the client(username) once it reach the threshold
            if login_success:
                s_message_dict["data"] = "Success"
                s_message_dict["address"] = self.clientAddress
                timestamp = str(datetime.datetime.now())[:19]
                record_etod_logbook(username, self.clientAddress, UDPPort,timestamp)
            else:
                self.login_faild_times[username] += 1
                s_message_dict["data"] ="Invalid Password"
                print(f"{username} {password} failed {self.login_faild_times[username]} times")
                
                if self.login_faild_times[username] >= max_login_fail_times:
                    login_block[username] = datetime.datetime.now() + datetime.timedelta(seconds=10)
                    s_message_dict["data"] = "Blocked"
        
        print(f"[send]: {s_message_dict}")
        s_message = json.dumps(s_message_dict)    
        self.clientSocket.send(s_message.encode())


print("\n===== Server is running =====")
print("===== Waiting for connection request from clients...=====")


while True:

    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
