from sys import exit, argv
from socket import *

def MessageRequest(ID,name,receiverName,Message): 
    """ the function is responsible for creating MessageRequest"""
    # total length of header including the first seven bytes of the fixed header. 
    # Magic No, ID, NameLen,ReceiverLen, MessageLen (they take up that much space no matter
    # what so thats why i added them first. 
    length_of_header = 16 + 8 + 8 + 8 + 16
    
    # then the client converts all the user name, receiver name, and Message into bits. 
    
    # name of server erson in bits 
    try: 
        name_in_bits = name.encode("utf-8")
    except UnicodeEncodeError:
        print("ERROR: Resopnse encoding error")
    # name of receiver person in bits
    try: 
        receiver_in_bits = receiverName.encode("utf-8")
    except UnicodeEncodeError:
        print("ERROR: Resopnse encoding error")    
    # name of message itself in bits 
    try: 
        message_in_bits = Message.encode("utf-8")
    except UnicodeEncodeError:
        print("ERROR: Resopnse encoding error")    
    
    # then using the len function the length of each of those previously converted vairables
    # was determiend and stored. 
    
    # lengths of header, name and reciever bytes. 
    namelenght = len(name_in_bits)
    receieverlen = len(receiver_in_bits)
    messagelen = len(message_in_bits)
    # finally using all of that information the totallength of the messagerequest is determiend. 
    # total length was determiend to work out the total length of the bytearray. 
    totalLength_of_messagerequest = length_of_header + namelenght  + receieverlen + messagelen
    # this is the messagerequest byte array that is sent from client to the server.and the length
    # of this array is the totalLengthOf the messagerquest.
    messagerequestarray =  bytearray(totalLength_of_messagerequest)
    # the magic number is as told. 
    MagicNo = 0xAE73
    # to put the magic number into the messagerequest array we essentially need to break 
    # into two pieces of 8 bits and then to move the first chunk we essentially move the 
    # magicNo to the right and the other half is moved to the second slot of the bytearary
    messagerequestarray[0] = (MagicNo >> 8)
    messagerequestarray[1] = MagicNo & 0xFF
    # the ID is already 8 bits so it can be put into the array slot 2 and same with name in bits and the receiver in bits 
    messagerequestarray[2] = ID
    messagerequestarray[3] = namelenght
    messagerequestarray[4] = receieverlen
    # similar to MagicNo setup
    messagerequestarray[5] = (messagelen >> 8)
    messagerequestarray[6] = (messagelen & 0xFF)
    # to put the rest of the bytes of the name, reciever and the message into the bytearray
    # the only reasons i tried this approch is because i don't konw how much i need to shift 
    # the individaul values by the only thing i know is the space it will take so i just used that to index and it worked. 
    messagerequestarray[7:7+namelenght] = name_in_bits
    messagerequestarray[7+namelenght : 7 + receieverlen +  namelenght] = receiver_in_bits
    messagerequestarray[7 + receieverlen + namelenght :] = message_in_bits
    return messagerequestarray


def askInputfromClient(): 
    """ the method returns two string tuple that contain the user inputs for the name of the receiver and the message itself"""
    name_of_receiver = input("enter the name of the receiver: ")
    while len(name_of_receiver) < 1 or len(name_of_receiver.encode("utf-8")) > 255:
        print("the name must be at least 1 charaacter and less than 255 bytes")
        name_of_receiver = input("please enter the name of the receiver: ") 
    
      
    message_content = input("enter the message: ") 
    while len(message_content) < 1 or len(message_content.encode("utf-8")) > 65535:
        print("The message must be at least 1 character and less than 65,535 bytes")
        message_content = input("enter the message: ")  
            
    return name_of_receiver, message_content



def readMessageResponse(response,sock,dictionaryOfUserNameAndMessage):
    """ this method is responsible for reading the message reesponse and checking for errors in it"""
    if (response[0] << 8 | response[1]) != 0xAE73:
        print("ERROR: magic number is not 0xAE73")
        return False

    if (response[2] != 3):
        print("ERROR: ID not = to 3")
        return False;
    
    if response[4] not in [0,1]:
        print("ERROR: MoreMsgs must be either 0 or 1")
        return False
  
    NumItem = response[3]
    if NumItem > 0: 
        # just an indexer to keep track of how many messages are being processed. 
        indexer = 0
        for i in range(NumItem):  
            try:
                response = sock.recv(3)
            except TimeoutError:
                print("ERROR: unable to read the first 3 bytes of the mesasge header")
                return False
           
            if(response[indexer] < 1):
                print("ERROR: senderLen must be at least 1")
                return False

            senderlen = response[indexer]
            indexer +=1
         
            if((response[indexer] << 8 | response[indexer + 1] ) < 1):
                print("ERROR: messagelen must be at least 1")
                return False
        
            messageLen = response[indexer] << 8 | response[indexer + 1]
         
            temporary = messageLen + senderlen 
            
            try: 
                response = sock.recv(temporary)
            
                try: 
                    userName = response[0:senderlen].decode("utf-8")
                except UnicodeDecodeError:
                    print("ERROR: response decoding failure during the storing process of the user name")
                    return False 
              
                try: 
                    Message = response[senderlen:].decode("utf-8")
                except UnicodeDecodeError:
                    print("ERROR: response decoding failure during the storage of the message")  
                    return False 
        
           
                if userName not in dictionaryOfUserNameAndMessage:
                    dictionaryOfUserNameAndMessage[userName] = [Message]
                else:
                   
                    dictionaryOfUserNameAndMessage[userName].append(Message)
                indexer = 0
          
            except TimeoutError:
                print("ERROR: unable to read the user name and message in time")
                return False
    return True


def Messagecontainsnothing(response):
    """ checks if the message packet actually contains the mesasge on not via the header info"""
    if response[3] == 0: 
        return True
    return False 
def MoreMegs(response):
    """just checks if the response consists of moremegs in it or not from the hedaer info"""
    if response[4] == 1: 
        return True
    return False

            
def main(): 
     
    sock = None 

    try: 
        
     
        if len(argv) != 5:
            print(f"Usage:\n\n\tpython(3) {argv[0]} <hostname> <port>\n")
            exit()   
   
        try: 
            port = int(argv[2])
           
            if ( 1024 > port or 64000 < port): 
                print("the port number is should be between 1024 and 64000")
                exit()
                
        except ValueError:
            print(f"ERROR: Port '{argv[2]}' is not an integer")
            exit() 

        name = argv[3]
        try: 
            if len(name) < 1 and len(name.encode("utf-8")) > 255:
                printf("client name is must be 1 character long and no longer than 255 bytes")
                exit()
        
         
        except UnicodeEncodeError: 
            print("ERROR: Response decoding failure")
            exit()
        requestType = argv[4]
        
        
        if requestType not in ["read", "create"]:
            print("ERROR: must type either read or create")
            exit()
            
    
        try: 
            services = getaddrinfo(argv[1],port,AF_INET,SOCK_STREAM)
            family,type, proto, canonname, address = services[0]
        except gaierror:
            print(f"ERROR: Host '{argv[1]}' does not exist or the IP address given in dotted-decimal motation is not well formed")
            exit()
    
        if requestType == "create":
            recievername, message = askInputfromClient()
            amount = MessageRequest(2,name,recievername,message)          
            print("Message has been sent") 


        if requestType == "read": 
            amount = MessageRequest(1,name,"","")
        
        sock = socket(AF_INET,SOCK_STREAM)
        sock.settimeout(1)
                 
        try:
            sock.connect(address)
            sock.send(amount)
            
            if requestType == 'read':
                try: 
                    headerOnly = sock.recv(5)    
                except TimeoutError: 
                    print("ERROR: message response is erroneous")
       
                dictionaryOfUserNameAndMessage = {}
                responsecheck = readMessageResponse(headerOnly,sock,dictionaryOfUserNameAndMessage)
                if responsecheck == True:
                
                    if Messagecontainsnothing(headerOnly) == True:
                        print("ERROR: no messages was sent to you.")
                        sock.close()
                    else:
                        counter = 1
                        for user,Message in dictionaryOfUserNameAndMessage.items():
                            if len(Message) > 1:
                                print(f"'{user}' has sent the following messages:")
                                for item in Message: 
                                    print(f"=> [{counter}] : '{item}'")
                                    counter += 1
                                counter = 0
                            else:
                                print(f"'{user}' has send the following message:\n=> [1] : '{Message[0]}'")
                        if MoreMegs(headerOnly) == True: 
                            print("There are still more messages to read from the server (run the client.py again to receive more messages) ") 
                            sock.close()
                                   
                else:    
                    print("ERROR: ether the message could not be processed within 1 second\n          or\n the sthe messege response from the server was invalid.")
                    sock.close()                        
            
        except TimeoutError: 
            print(f"ERROR: unable to connect")
            exit()
              
   
    finally: 
        if sock != None: 
            sock.close()
            exit()
main()
