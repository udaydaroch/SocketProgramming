from sys import exit, argv
from socket import *
"""name = Uday Daroch
   studentID = 24999340
"""

def messageResponse(ID,requestedUser,dictionaryOfMessages,connection): 
    # the length_of_header stores length of the intial header consisting of the 
    # magic Num, ID, NumItems, MoreMsgs. the will alwyas take that much spaces so 
    # i just simply added them intially 
    # 16 from Magic number, 8 from ID and so on.
    length_of_header = 16 + 8 + 8 + 8
    
    # the moremsgs is intialized to 0 because it is unkown in the begining (as well as NumItems).
    MoreMsgs = 0
    NumItems = 0
    
    # then it is checked how many messages the serve has for the requested user. 
    # if there are more then 255
    # the moremsgs number is turned to 1 as specfied in the 3.3 section. 
    # and the NumItems is set to 255
    # otherwise the NumItems (if the number of messages is less than or equal to 255
    # the NumItems is just the length of the numberofmesssage stored for that particular user.
    if requestedUser not in dictionaryOfMessages:
        MoreMsgs = 0
        NumItems = 0
    elif len(dictionaryOfMessages[requestedUser]) > 255:
        MoreMsgs = 1
        NumItems = 255
    else:
        NumItems = len(dictionaryOfMessages[requestedUser])
    
    #  the messageResponsebytearray intially contained 5 bytes of slots for the headers.
    messageResponseArray = bytearray(5)

    # here the server is just adding all the header info into the bytearray( which contains just enough room to fit all of the info).
    MagicNo = 0xAE73
    messageResponseArray[0] = (MagicNo >> 8)
    messageResponseArray[1] = MagicNo & 0xFF
    
    messageResponseArray[2] = ID
    messageResponseArray[3] = NumItems
    messageResponseArray[4] = MoreMsgs
    
    # onces the packet is ready i am sending it to the client straight away. 
    
    # here the server is just creating tempearary varaibles to store values temperaraoly so that they can be stroed inside the tempbytearray.
    messagelen = 0
    senderlen = 0
    tempByteArray = bytearray()
    
    # before getting into the loop I am just checking if there are actually any messages in the first place if there aren't i am not going through the loop and just going straight to the return statement which returns the NumOfItems and and hence the client only receives the messageResponse array consisting of only the 5 slot header info. 
    if NumItems > 0: 
        # i am interating using a for loop through the number of items there are after the check. 
        # i then go through the actual dictionary of Messages (specfically through the the requestUser. ) and do the following steps. 
        
        # access the sender and the message stored in the tuple. 
        # store their lengths after they are converted into bytes. 
        # summing all the length inclduding the allocated values for the senderlen(8) and message len(16) and assinging that value to the etempByteArrayLen 
        # making the tempByteArray with tempByteArrayLen as the num of slots avaialbe. 
        # storing the values inside the array and send the packet acrros to the client as soon as the packet is created. 
        #This is done for all sender and messages in one packet.
        
        temp_indexer = 5
        
        restOfMessages = bytes()
        for senderandMessages in dictionaryOfMessages[requestedUser][0:NumItems]:
            
            senderName = senderandMessages[1].encode("UTF-8")
            Message = senderandMessages[0].encode("UTF-8")
            messagelen = len(Message)
            senderlen = len(senderName)
            
            tempByteArrayLen = 8 + 16 + senderlen + messagelen
            tempByteArray = bytearray(tempByteArrayLen)
    
            tempByteArray[0] = senderlen
            tempByteArray[1] = (messagelen >> 8)
            tempByteArray[2] = messagelen & 0xFF
            tempByteArray[3:3+senderlen] = senderName
            tempByteArray[3+senderlen:] = Message
        
            dictionaryOfMessages[requestedUser].pop(0)
            messageResponseArray.extend(tempByteArray)  
    # onces all the packaging is done the messagreResponse array is sent to the client 
    # via the connection socket. 
    
        
    return NumItems,messageResponseArray


def MessageRequestprcoess(message,conn):
    """this function follows the process described in section 3.3"""
    
    # if all the checks pass the function returns true otherwise as suggested in the assignment -> the socket obtained from accept() is closed and returns false. 
    
    #– message must contain at least 7 bytes. if its less than that it measn the packet 
    # it recieves is not constructed correctly(not following the protocol)
    if(len(message) < 7):
        print("ERROR: message len less than seven")
        conn.close()
        return False 
    
    # here the server is just extrracting the values from the packet as described in the message request 
    MagicNo = message[0] << 8 | message[1]
    I_D = message[2]
    NameLen = message[3]
    Recievelen = message[4]
    MessageLen = message[5] << 8 | message[6]
    
    #– The contents of the ‘MagicNo’ field must equal 0xAE73.
    if MagicNo != 0xAE73:
        print(f"ERROR: MagicNo is wrong {hex(MagicNo)}")
        return False 
    #- The contents of the ‘ID’ field must be either 1 or 2.
    if I_D not in [1,2]: 
        print("ERROR: ID not in 1 or 2")
        return False
    
    #– The contents of the ‘NameLen’ field must be at least 1.
    if NameLen < 1:
        print("ERROR: NameLen is not at least 1")
        return False 
    #– The contents of the ‘ReceiverLen’ field must be 0 if ‘ID’ is 1 (read request), or at least 1 if ‘ID’ is 2(create request).
    if (I_D == 1 and Recievelen != 0) or (Recievelen < 1 and  I_D == 2):
        print("ERROR: Reciever length is not sufficent")
        return False 
 
    # – Similarly, the ‘MessageLen’ field must be 0 if ‘ID’ is 1, or at least 1 if ‘Type’ is 2.    
    if(MessageLen != 0 and I_D == 1) or (MessageLen < 1 and I_D == 2):
        print("ERROR: Message lenght is not sufficent")
        return False 

    # it only returns true if all the checks have passed 
    return True


def createRequest(message,reserver_storage,conn):
    """responsible for handling createRequest functionaility"""
    # first using message(bytearray) we extract the sender name, the receiver name, and the message recieved. using array indexing. 
    try: 
        restOfMessage = conn.recv(2**17)
    except TimeoutError:
        print("ERROR: timeout error")
    
    sender =  restOfMessage[0:message[3]].decode("utf-8")
    reciver_name = restOfMessage[message[3]:message[4] + message[3]].decode("utf-8")
    message_received = restOfMessage[message[3] + message[4]:].decode("utf-8")
    
    NameLen = message[3]
    Recievelen = message[4]
    MessageLen = message[5] << 8 | message[6]

    expected = NameLen + Recievelen + MessageLen
    recieved = len(sender) + len(reciver_name) + len(message_received)
    if expected != recieved:
        print(f"ERROR: expected {expected} bytes")
        print(f"       received {recieved} bytes")
        
    # as per the reuqirements the following print statments print out an information message suggesting that the mesage request has been recieved and the name of the sender and the reciever. 
    print("Message request recieved")
    print("sender name: ", sender)
    print("reciever name: ", reciver_name)
    conn.close() 
    
    # this is a simple way to check if the reicever is actually in reservestorage dictionary or not 
    
    # if its not a list is generatored storing the message_received, sender tuple
    # if the name is in the list then the tuple is simply appended to the list that was intially generated for that reciever name as the keys' value. 
    if reciver_name not in reserver_storage:  
        reserver_storage[reciver_name] = [(message_received, sender)]
    else: 
        reserver_storage[reciver_name].append((message_received, sender))  
    # finally the socket was closed as described. 
    conn.close()
    
def readRequest(message,reserver_storage, conn):
    """responsible for handling readRequest functionaility"""
    
    # the method first extracts the request user name 
    try: 
        restOfMessage = conn.recv(len(message))
    except TimeoutError:
        print("ERROR: unable to read from the socket (timeout)")
        
    requested_user = restOfMessage[0:message[3]].decode("utf-8")
    # it then called the messageResopnse function passing in 
    # the ID value which is 3, the request user name, the dcitionary storing users, and the conn socket itself. 
    messageAndNumOfItems = messageResponse(3,requested_user,reserver_storage,conn)
    
    # the messageResponse returns the numofItems being sent and then simply just prints out 
    # an informative message to the server user informing how many messages were sent to the request user and the name of the request user. 
    NumOfItems = messageAndNumOfItems[0]
    Message =  messageAndNumOfItems[1]
    
    print("Message response sent")
    if NumOfItems > 1:
        print(f"{NumOfItems} messages sent to {requested_user}.")
    elif NumOfItems == 1:
        print(f"{NumOfItems} message sent to {requested_user}.")
    else:
        print(f"{NumOfItems} messages sent to {requested_user}.")
    # finally the conn socket is closed 
    return Message

def main(): 
    # intializing the sock and conn sockets to None
    sock = None 
    conn = None 
    # the reserver_storage is just a dictionary that stores the the mesages and the sender name under the reciever name. 
    reserver_storage = {}
    
    # checking if the arguments passed to the command line are at least 2 else prints an error.
    if len(argv) != 2:
        print(f"Usage:\n\n\tpython(3) {argv[0]} <port>\n")
        exit()
    
    # the server then extracts the port number from the argument passed to the command line and attempts to convert it to a number.
    # otherwise a ValueError is detected by the except block.
    # if the port number is an integer and not between the required range the port number is not accepted
    # an error message is generated.
    # in either options the exit function is called. 
    try: 
        port = int(argv[1])
        if ( 1024 > port or 64000 < port): 
            print("ERROR: the port number is should be between 1024 and 64000")
            exit()
    except ValueError: 
        print("ERROR: the port number is not a number")
        exit()
    
   

    # using the socket import the server creates a socket  and assignes it to the previously 
    #created varaible called sock. 
    
    # by passing the attributes told in class 
    # AF_INIT which is the addres from the internet address that the socket can communcate with
    # along with the socket_stream which is for the TCP server(two way stream). 
    
    sock = socket(AF_INET,SOCK_STREAM)
    # FIRST BULLET POINT>
    # this try block was used to check if the binding happens successfully.if its doesn't an error message is generated. 
    try: 
        sock.bind(("0.0.0.0", port))

    except OSError as bind_error: 
        print(f"ERROR: Could not bind the socket to port:{bind_error}") 
        exit()
        
    # SECOND BULLET POINT this is just a listen try block and if it doesn't work the ERROR message is printed suggesting that the call listen on the socket. if this doesn't work
    # the sock is closed and the exit function is called. 
    try: 
        sock.listen(5)
    except OSError as listen_error: 
        print(f"ERROR: unable to call listen on the socket : {listen_error}") 
        sock.close()
        exit()
        
    # here the server enters an infinite loop. 
    while True:
  
        # BULLET POINT 3
        
        
        # the accept function is used to intialize a new connection which returns the
        #conn(the varaible that was initially assigned ot none is not attached to the connecting socket)
        # and the client.
        # for logging purpose (as suggested) the server prints a message indicating the IP 
        # address and the port number of the client from which the incoming connection 
        # orginated 
        
        #BULLET POINT 3 point 1 
      
      
        # BULLET POINT 3 point 3 
        # the following try block is important becasue it first checks whether the socket
        # conn has actually received data.
        # then we set a timeout for the conn socket. 
        # this tyr block also take in account whether the record is:
        # A) --> valid (by calling the message request process function)
        # B) --> it also checks if the required number of bytes for the complte reuqest can or cannot be read rfom the scoket within a max of one second after accept().

        # also if during the recv() calll if the method fails to retrieve the data(in this case a bytearray) within 1 second sther eis another timout error that gets handled in the except block (as suggested by the section3.5)
        
        conn, client = sock.accept()
        # (another time out is set but this time for the conn socket as mentioned by section 3.5) 
        conn.settimeout(1)
        print(f"client IP address: {client[0]} port : {client[1]}")

        
        try: 
            message = conn.recv(7)
            # if this is possible without a timeout we process the message by calling the message request process(which carried out the prcoess described in section 3.3) 
            # the server checks the validity of the message.
            #BULLET POINT 3 point 2
        # if the message can't be processed in time period or if the packet was invalid. 
        except TimeoutError: 
            print("ERROR: unable to read from the socket on time (timeout)")
            conn.close()
            return
        
        if MessageRequestprcoess(message,conn) != True:
            conn.close() 
            
        # the following statemnts checks the type of request we have.
        # we first extract the message request value from the 2 slot of the bytearray we received from the conn socket. 
        # depending on the type of request( 1 for read and 2 for create) received certain function are called.
        
        request = message[2]
        if request == 2:
            # calls the createRequest function that is responsible for handling createRequest tasks 
            # passing the message(bytearray received), the reserve storage dictionary and the conn socket it self. 
            createRequest(message, reserver_storage,conn)
            continue
        
        elif request == 1:
            # calles the readRequest 
            # same parameters are passed to the readRequest function however the function is different(explained in the function itself).
        
            message = readRequest(message,reserver_storage, conn)
            conn.send(message)
            continue
        
main()
        

    