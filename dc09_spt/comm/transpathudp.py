# ----------------------------
# Transmit class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import socket
import logging


class TransPathUDP:
    def __init__(self, host, port,  timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.s = None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.settimeout(self.timeout)
        except Exception as e:
            self.s = None
            logging.error('UDP Socket creation exception %s',  e)
        return self.s
        
    def send(self, msg):
        if self.s is not None:
            try:
                self.s.sendto(msg, (self.host, self.port))
            except Exception as e:
                self.s = None
                logging.error('UDP send message to host %s port %s exception %s',  self.host,  self.port,  e)
    
    def receive(self, length=1024):
        antw = None
        if self.s is not None:
            try:
                antw,  sender = self.s.recvfrom(length)
            except Exception as e:
                self.s = None
                logging.error('UDP receive message from host %s port %s exception %s',  self.host,  self.port,  e)
        return antw

    def sendAndReceive(self, msg,  max_antw=1024):
        antw = None
        if self.s is not None:
            try:
                self.s.settimeout(self.timeout / 5)
                for x in range(5):
                    try:
                        self.s.sendto(msg, (self.host, self.port))
                        antw,  sender = self.s.recvfrom(max_antw)
                        if sender[1] != self.port:
                            antw = None
                    except Exception as e:
                        if e != TimeoutError:
                            raise
                        else:
                            pass
                    else:
                        break
            except Exception as e:
                self.s = None
                logging.error('UDP message exchange to host %s port %s exception %s',  self.host,  self.port,  e)
            if antw is None:
                logging.error('UDP message exchange to host %s port %s timeout',  self.host,  self.port)
        return antw

    def disconnect(self):
        if self.s is not None:
            self.s.close()
            self.s = None
