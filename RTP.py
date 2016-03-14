import socket as sk
import sys
from select import select
import random
import struct

ACK = int('00000001', 2)
SYC = int('00000010', 2)
FIN = int('00000100', 2)
ERR = int('00001000', 2)

headerStruct = struct.Struct('I I h')#sequence num, ACK num, control bits plus data

class RTPSocket(object):
    """docstring for socket"""
    def __init__(self,soc=None,closeCallback=None):
        super(RTPSocket, self).__init__()
        if soc==None:
            self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        else:
            self.socket = soc
            self.closeCallback = closeCallback
        self.connectionRequest = []
        self.currentConnection = {}

    def connect(self,address):
        controlBits = SYC
        self.base = random.randint(0,10**8)
        header = headerStruct.pack(self.base, 0, controlBits)
        msg = ''
        self.socket.sendto(header+msg,address)
        print 'fist hand shake sent'
        connected = False
        self.socket.settimeout(3)
        try:
            #try to connect and it could timeout or fail
            while (not connected):
                inputready,outputready,exceptready = select([self.socket],[],[])
                for each in inputready:
                    request2, address2 = self.socket.recvfrom(2048)
                    msglen = len(request2) - headerStruct.size
                    self.serverSeq, ack, ctl, msg = struct.Struct(headerStruct.format+" "+str(msglen)+'s').unpack(request2)
                    if not ctl == (SYC|ACK) :
                        if ctl & ERR:
                            print msg
                        else:
                            print 'unknown error'
                        raise Exception('Connection error', 'Wrong response code')
                    if not ack == self.base+1:
                        raise Exception('Connection error', 'Wrong ACK')
                    print 'good second hand shake'
                    self.address = address2
                    self.base = self.base+1
                    self.serverSeq = self.serverSeq + 1
                    header = headerStruct.pack(self.base, self.serverSeq, ACK)
                    msg = ''
                    self.socket.sendto(header+msg,self.address)
                    connected = True
                    self.socket.settimeout(None)
                    break
        except Exception, e:
            print 'connectionRequest timeout!'
            raise e
    
    def accept(self):
        if len(self.currentConnection)<self.maxConnection:
            newConnection = self.createNewConnection()
            if newConnection:
                self.currentConnection[newConnection.address]= newConnection
            else:
                print "Failed to establish connection"
            return newConnection
        else:
            #reject
            request, address = self.socket.recvfrom(2048)
            header = headerStruct.pack(0, 0, ERR)
            self.socket.sendto(header + 'Connection is full',address)
            print "Connection is full"
            return None
        pass

    def createNewConnection(self):
            request, address = self.socket.recvfrom(2048)
            msglen = len(request) - headerStruct.size
            self.clientSeq, ack, ctl, msg = struct.Struct(headerStruct.format+" "+str(msglen)+'s').unpack(request)
            self.clientSeq = self.clientSeq+1
            if not ctl & SYC:
                return None

            newSocket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
            newSocket.settimeout(1)

            self.base = random.randint(0,10**8)
            header = headerStruct.pack(self.base, self.clientSeq, SYC|ACK)
            msg = ''
            newSocket.sendto(header+msg,address)
            while (1):
                #should have timeout here to prevent infinite wait
                # try:
                    request2, address2 = newSocket.recvfrom(2048)
                    if not address2 == address:
                        #possible port scan
                        continue
                except Exception, e:
                    print "timeout: ", e 
                    #time out  what should do??????
                    newSocket.close()
                    return None

                clientSeq, ack, ctl, msg = struct.Struct(headerStruct.format+" "+str(msglen)+'s').unpack(request2)
                
                if  ack==self.base+1 and ctl&ACK:
                    self.base = ack+1
                    self.clientSeq = clientSeq
                    newSocket.settimeout(None)
                    connectedSocket = self.__class__(soc=newSocket,closeCallback=self.__closeConnection)
                    connectedSocket.address = address2
                    return connectedSocket
                else: 
                    return None

    def bind(self,address):
        self.address = address
        self.socket.bind(address)
        pass

    def listen(self,num):
        self.state = 'passive'
        self.maxConnection = num
        pass    

    def fileno(self):
        return self.socket.fileno()

    def __closeConnection(self,address):
        closingConnection = self.currentConnection.pop(address)
        # print closingConnection
        # closingConnection.close()
        pass
    def close(self):
        header = headerStruct.pack(0, 0, FIN)
        newSocket.sendto(header,self.address)
        
        if self.closeCallback:
            self.closeCallback((self.address))
        self.socket.close()

    def send(self, msg):
        #break long msg into packets
        self.socket.sendto(msg,self.address)
        return len(msg)

    def recv(self,length):
        #should check close signal
        while (1):
            inputready,outputready,exceptready = select([self.socket],[],[])
            for each in inputready:
                msg, address = each.recvfrom(length)
                # if address == self.address:
                return msg

 
                
