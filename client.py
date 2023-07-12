"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
    Author: Xiaoyang Duan z3360376
"""
from code import interact
from re import S
from socket import *
import sys
import json
import os
from threading import Thread


def UDP_reciever():
    #print(f"UDP start listening from({my_UDP_IP}, {my_UDPPort})")
    while True:
        reciever = socket(AF_INET, SOCK_DGRAM)
        reciever.bind((my_UDP_IP,my_UDPPort))
        message, address = reciever.recvfrom(1024)
        print("we get message from address:",address)
        print(message.decode('utf-8'))
        print("Enter one of the following commands (EDG, UED, SCS, DTE, AED, UVF, OUT):")
        reciever.sendto(f"Hi, this message from address({my_UDP_IP},{my_UDPPort}), your message already recieved!".encode('utf-8'), address)




def edg_func(username,fileID,dataAmount):
    file_name =str(username) +"-"+ str(fileID)+".txt"
    with open(file_name,"w+") as file:
        for i in range(int(dataAmount)):
            file.write(str(i+1)+"\n")
    print(f"done, {dataAmount} data samples have been generated and stored in the file {file_name}")

def ued_func(username,fileID):
    
    file_name =str(username) +"-"+ str(fileID)+".txt"
    if os.path.exists(file_name):
        with open(file_name,"r") as file:
            content = file.read()
        print(f"done, data have been read successfully from {file_name}")
        return content
    else:
        print("the file to be uploaded does not exist")

def interact_server(s_message_dict):
    #print("[send]:",s_message_dict)
    s_message = json.dumps(s_message_dict) 
    clientSocket.sendall(s_message.encode())

    #r_data = clientSocket.recv(1024)
    r_message = clientSocket.recv(1024).decode()
    r_message_dict = json.loads(r_message)
    #print("[recv]:",r_message_dict)

    return r_message_dict
        
    


#Server would be running on the same host as Client
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_IP SERVER_PORT ======\n")
    exit(0)
serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
my_UDPPort =int(sys.argv[3])
serverAddress = (serverHost, serverPort)

# define a socket for the client side, it would be used to communicate with the server
clientSocket = socket(AF_INET, SOCK_STREAM)

# build connection with the server and send message to it
clientSocket.connect(serverAddress)

#login for the first time
r_message = ""
#r_message_dict ={}

s_message_dict = {}
s_message_dict["act"] = "login"
s_message_dict["username"] = input("Username:")
s_message_dict["password"] = input("Password:")
s_message_dict["UDPPort"] = my_UDPPort

s_message = json.dumps(s_message_dict)
#print("[send]: ",s_message_dict)

clientSocket.sendall(s_message.encode())

#while loop for login
while True:

    #r_data = clientSocket.recv(1024)
    r_message = clientSocket.recv(1024).decode()
    r_message_dict = json.loads(r_message)

    #print("[recv]:",r_message_dict)

    if r_message_dict["data"] == "Invalid Password":
        s_message_dict["password"] = input("Password:")

    elif r_message_dict["data"] =="Success":
        my_UDP_IP = r_message_dict["address"][0]
        print("login successfully!")
        username = s_message_dict["username"]
        break

    elif r_message_dict["data"] == "Blocked":
        dict.clear(s_message_dict)
        print("Invalid Password. Your account has been blocked. Please try again later")           
        s_message_dict["act"] = "exit"
    
    elif r_message_dict["data"]=="Blocked & Wait":
        dict.clear(s_message_dict)
        print("Your account is blocked due to multiple authentication failures. Please try again later")          
        s_message_dict["act"] = "exit"
    
    else:
        dict.clear(s_message_dict)
        print("login-loop: not defined [recv] {r_message}\n")
        s_message_dict["act"] = "exit"

    #print("[send]:",s_message_dict)
    s_message = json.dumps(s_message_dict)
    clientSocket.sendall(s_message.encode())

    #if client silde can't login successfully, we just disconnect the end the program
    if r_message_dict["act"]!="login" or s_message_dict["act"] == "exit":
        clientSocket.close()
        sys.exit(0)
        #break
     

#set a thread to keep listening from the other clients
UDP_thread =Thread(target=UDP_reciever,daemon=True)
UDP_thread.start() 


#login successfully, then we take the action
new_active_edge_list =[]
while True:

    dict.clear(s_message_dict)
    rough_input = input("Enter one of the following commands (EDG, UED, SCS, DTE, AED, UVF, OUT):\n")
    s_message_dict["act"] = rough_input.split(" ")[0]

    # if s_act = "EDG" we don't need to interact with the server
    if s_message_dict["act"] == "EDG":

        if len(rough_input.split())!=3:
            print("the command should in format [UED (fileID) (dataAmount)]")
        else:
            fileID = rough_input.split(" ")[1]
            dataAmount = rough_input.split(" ")[2]  
            if fileID.isnumeric() and dataAmount.isnumeric():
                edg_func(username,fileID,dataAmount)
            else:      
                print("the fileID or dataAmount are not integers, you need to specify the parameter as integers")
    
    elif s_message_dict["act"] == "exit":

        #print("[send]:",s_message_dict)
        s_message = json.dumps(s_message_dict)
        clientSocket.sendall(s_message.encode())
        break
    
    #if s_act is not "EDG" we need to interact with server
    else:
        if s_message_dict["act"] == "UED":
            if len(rough_input.split(" ")) == 1:
                print("fileID is needed to upload the data")
            elif len(rough_input.split(" ")) > 2:
                print("the command should in format [UED (fileID)]")
            else:

                fileID = rough_input.split(" ")[1]
                if fileID.isnumeric():
                    s_message_dict["fileID"] = fileID
                    s_message_dict["data"] = ued_func(username,fileID)
                    
                    if s_message_dict["data"] != None:
                        r_message_dict = interact_server(s_message_dict)

                        if r_message_dict.get("data") == "Success":
                            print(f"Data file with ID of {fileID} has been uploaded to server")
                        else:
                            print(f"Data file with ID of {fileID} not uploaded to server")
                else:
                    print("fileID is not integer, you need to specify the parameter as integer")

        elif s_message_dict["act"] == "SCS":
            SCS_check_list =[ "AVERAGE","MAX","MIN","SUM"]
            if len(rough_input.split(" ")) != 3:
                print("the command should in format [SCS (fileID) AVERAGE/MAX/MIN/SUM]")
            else:
                s_message_dict["fileID"] = rough_input.split(" ")[1] 
                s_message_dict["opration"] = rough_input.split(" ")[2]

                if s_message_dict["fileID"].isnumeric() == False:
                    print("fileID is missing or fileID should be an integer")

                elif s_message_dict["opration"] not in SCS_check_list:
                    print("the computation operation only choose from AVERAGE/MAX/MIN/SUM")
                
                else:
                    r_message_dict = interact_server(s_message_dict)
                    if r_message_dict.get("data") == None:
                        print("the file is not exist on server side")
                    else:
                        print("Computation(",s_message_dict["opration"],")result on the fileID",s_message_dict["fileID"], f"returned from the server is:", r_message_dict["data"] )

        elif s_message_dict["act"] =="DTE":
            if len(rough_input.split(" "))!=2:
                print("the command should in format [DTE (fileID)]")
            else:
                s_message_dict["fileID"] = rough_input.split(" ")[1]
                if s_message_dict["fileID"].isnumeric() == False:
                    print("fileID is missing or fileID should be an integer")
                else:
                    r_message_dict = interact_server(s_message_dict)
                    if r_message_dict.get("data") == "Success":
                        print("file with ", s_message_dict["fileID"], " of fileID has been successfully removed from the central server")
                    else:
                        print("the file does not exist at the server side")


        elif s_message_dict["act"] =="AED":
            if len(rough_input.split(" "))!= 1:
                print("too many arguments, the command should in format [DTE]")
            else:
                r_message_dict = interact_server(s_message_dict) 
                if r_message_dict.get("data") != []:
                    new_active_edge_list = r_message_dict["data"]
                    for row in r_message_dict["data"]:
                        print(row)
                else:
                    print("no other active edge devices")
        
        elif s_message_dict["act"] =="OUT":
            if len(rough_input.split(" "))!= 1:
                print("too many arguments, the command should in format [OUT]")
            else:
                r_message_dict = interact_server(s_message_dict) 
                if r_message_dict.get("data") == "Success":
                    print("Bye!",username)
                    break
        
        elif s_message_dict["act"] == "UVF":
            right_username = False
            if len(rough_input.split(" "))!= 3:
                print("the command should in format [UVF reciever_username short_massage]")
            else:
                for info in new_active_edge_list:
                    if info.split("; ")[2] == rough_input.split(" ")[1]:
                        right_username = True
                        r_UDP_IP = info.split("; ")[3]
                        r_UDPProt = int(info.split("; ")[4])
                
                if right_username:
                    sender = socket(AF_INET, SOCK_DGRAM)
                    print(f"we are sending to address {r_UDP_IP},{r_UDPProt}")

                    UDP_message = rough_input.split(" ")[2]
                    sender.sendto(UDP_message.encode('utf-8'),(r_UDP_IP,r_UDPProt))
                    print(sender.recvfrom(1024)[0].decode('utf-8'))
                else:
                    print("wrong reciever_username")
                    
                        
        else:
            print("type 'OUT' if you want to leave")



# close the socket
clientSocket.close()
sys.exit(0)
