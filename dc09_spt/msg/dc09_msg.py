# ----------------------------
# Class to implement the SIA DC09 block
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import datetime
import random
from Crypto.Cipher import AES


class dc09_msg:
    """
    SIA DC09 message block implementation
    
    This class serves to build a message block from an DC07 payload message as constructed in:
    dc03_msg for an DC03 (SIA) message formatted for DC07
    or
    dc05_msg for an RC05 (Ademco Contact ID) message formatted for DC07
    
    1.  convert a map with values to a valid DC09 message
    2.  pack a DC09 message into a message block.
        If an encryption key is provided the message block will be encrypted
        calling without an DC09 message will result in a poll block
    
    An received answer package can be decrypted if needed and checked.

    Copyright (c) 2018  van Ovost Automatisering b.v.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
    """ 
    def __init__(self, account,  key=None,  receiver=None,  line=None, offset=0):
        """
        dc09_msg class initialisator
       
        parameters
            account
                account number as a string. For most receivers it needs to be numeric and have a max length.
                the standard allows 4 to 10 positions numeric or upper case.
            key
                the optional encryption key in either 16 or 32 bytes 
            receiver
                an optional integer to be used as receiver number in the block header
            line
                an optional integer to be used as line number in the block header
            offset
                the time offset for this receiver in seconds
        """
        self.account = account
        self.key = key
        self.receiver = receiver
        self.line = line
        self.offset = offset
        if self.key is not None and len(self.key) != 16 and len(self.key) != 32:
            raise Exception('Keylength is {} but must be either 16 or 32'.format(len(key)))
    
    @staticmethod
    def dc09crc(data):
        """
        Static method to calculate CRC16 According to SIA DC07
        """
        def calc_crc(crc, debyte):
            deze = ord(debyte)
            for i in range(0, 8):
                deze ^= crc & 1
                crc >>= 1
                if deze & 1:
                    crc ^= 0xa001
                deze >>= 1
            return crc
        crc = 0
        for j in range(0, len(data)):
            crc = calc_crc(crc, data[j])
        return crc
        
    def dc09crypt(self,  data):
        """
        Encrypt -data- with -key- in AES CBC mode
        """
        crypt = ''
        pad = (len(data) + 21) % 16
        for i in range(0, 17-pad):
            rnd = '['
            while rnd == '[' or rnd == ']' or rnd == '|':
                rnd = chr(random.randint(20, 125))
            crypt += rnd
        now = datetime.datetime.utcnow()+datetime.timedelta(seconds=self.offset)
        crypt += data + '_{:%H:%M:%S,%m-%d-%Y}'.format(now)
        iv = 16 * chr(0)
        encryption_suite = AES.new(self.key, AES.MODE_CBC, iv)
        return encryption_suite.encrypt(crypt)

    def dc09decrypt(self,  data):
        """
        Decrypt -data- with -key- in AES CBC mode
        """
        if len(data) % 16 != 0:
            raise Exception('Data length not a multiple of 16')
        iv = 16 * chr(0)
        encryption_suite = AES.new(self.key, AES.MODE_CBC, iv)
        return encryption_suite.decrypt(data)

    def dc09block(self,  msg_nr=0,  dc09type="NULL",  msg="]"):   
        """
        Construct a DC09 message block
        
        Parameters:
            msg_nr
                the message number has to be incremented from 0001 to 9999 for each message
            dc09type
                the type defines the payload
                currently available types are 'SIA-DCS' , 'ADM-CID' and 'NULL'
                the default is 'NULL' for a poll block
            msg
                the payload of the block.
                the payload should correspond to the type 
                for 'ADM-CID' it is the result of dc05event
                for 'SIA-DCS' it is the result of dc03event
                for 'NULL' it is ']' , which is the default value.
                
                the payload may be extended with the extra data constructed with dc09_extra
        """
        if self.key is None:
            ret = '"' + dc09type + '"'
        else:
            ret = '"*' + dc09type + '"'
        ret += '{0:04X}'.format(msg_nr)
        if self.receiver is not None:
            ret += 'R{0:X}'.format(self.receiver)
        if self.line is not None:
            ret += 'L{0:X}'.format(self.line)
        ret += '#' + self.account + '['
        if self.key is None:
            ret += msg
        else:
            if type != "NULL":
                msg = '|' + msg
            ret += self.dc09crypt(msg).hex().upper()
        ret = '\n' + '{0:04X}'.format(self.dc09crc(ret)) + '{0:04X}'.format(len(ret)) + ret + '\r'
        return ret

    def dc09poll(self):
        """
        Construct a DC09 poll block
        """
        return self.dc09block()

    def set_offset(self, offset):
        """
        set the time offset in seconds for this receiver
        """
        self.offset = int(offset)

    def dc09answer(self,  msg_nr,  answer):
        """
        Check the validity of the answer block
        
        Parameters:
            msg_nr  
                the expected message number
            answer
                the received answer block
        Return values
            [0]
                the answer ('ACK', 'NAK', 'DUH' or RSP')
            [1]
                the calculated time offset for this receiver in seconds
        """
        alen = len(answer)
        if alen < 10:
            raise Exception("Answer too short")
        length = int(answer[5:9], 16)
        if length != alen - 10:
            raise Exception("Answer length ({0}) not equals content of message {1}".format(alen, length))
        crc = self.dc09crc(answer[9:-1])
        i = int(answer[1:5], 16)
        if crc != i:
            raise Exception("CRC of Answer incorrect")
        if answer[10] == '*':
            mnr = int(answer[15:19], 16)
            ret = answer[11:14]
        else:
            mnr = int(answer[14:18], 16)
            ret = answer[10:13]
        if mnr != msg_nr and ret != 'NAK':
            raise Exception("Invalid message number")
        offset = None
        if answer[10] == '*':
            bracket = answer.find('[')
            ct = bytes.fromhex(answer[bracket+1:alen-1])
            answer = self.dc09decrypt(ct)
            answer = answer[-21:].decode()
        tm = None
        if len(answer) > 22 and answer[-22:-20] == ']_':
            tm = answer[-20:-1]
        if len(answer) > 20 and answer[-21:-19] == ']_':
            tm = answer[-19:]
        if tm is not None:
            now = datetime.datetime.utcnow()
            receivertime = datetime.datetime.strptime(tm, "%H:%M:%S,%m-%d-%Y")
            offset = (receivertime-now).total_seconds()
        return ret, offset

    @staticmethod
    def dc09_extra(params={}):   
        """
        Static method to construct an extra data block according to DC09
        
        Parameters
            params
                a map containing key-value pairs.
                currently implemented are :
                'lon'
                    the longitude where the event was generated as a string e.g. '52.21'
                'lat'
                    the latitude where the event was generated as a string e.g. '5.9699'
                'mac'
                    the mac address of the network interface in string format
                'verification'
                    an internet or intranet adress to access alarm verification information e.g. a camera
        """
        extra = ''
        if 'lon' in params:
            extra += '[X' + params['lon'] + ']'
        if 'lat' in params:
            extra += '[Y' + params['lat'] + ']'
        if 'mac' in params:
            extra += '[M' + params['mac'] + ']'
        if 'verification' in params:
            extra += '[V' + params['verification'] + ']'
