# ----------------------------
# Dialler class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
from dc09_spt.msg.dc09_msg import *
from dc09_spt.msg.dc05_msg import *
from dc09_spt.msg.dc03_msg import *
import time
import threading
from collections import deque
import logging
from dc09_spt.comm.transpath import TransPath


class dc09_spt:
    """
    Handle the basic tasks of SPT (Secured Premises Transciever)

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

    def __init__(self, account, receiver=None, line=None):
        """
        Define a basic dialler (SPT Secure Premises Transceiver)
        
        parameters
            account
                Account number to be used. 
                Most receivers expect a numeric string of 4 to 8 digits
            receiver
                an optional integer to be used as receiver number in the block header
            line
                an optional integer to be used as line number in the block header
        """
        self.account = account
        self.receiver = receiver
        self.line = line
        self.tpaths = {
            'main': {
                'primary': {
                    'path': None,
                    'ok': 0
                },
                'secondary': {
                    'path': None,
                    'ok': 0
                }
            },
            'back-up': {
                'primary': {
                    'path': None,
                    'ok': 0
                },
                'secondary': {
                    'path': None,
                    'ok': 0
                }
            },
        }
        self.tpaths_lock = threading.Lock()
        self.backup_prim = None
        self.backup_sec = None
        self.main_ok = False
        self.backup_ok = False
        self.main_poll = None
        self.backup_poll = None
        self.msg_nr = 0
        self.queue = deque()
        self.queuelock = threading.Lock()
        self.running = False
        self.poll = None
        self.send = None
        self.counter = 0
        self.counterlock = threading.Lock()
        self.routines = []
        self.routines_changed = 0
        self.poll_active = 0
        self.msg_callback = None

    # ---------------------
    # configure transmission paths
    # ---------------------
    def set_path(self, mb, pb, host, port, *, account=None, key=None, receiver=None, line=None, type=None):
        """
        Define the transmission path 
        
        parameters
            main/back-up
                value 'main' or 'back-up'
            primary/secondary
                value 'primary' or 'secondary'
            host
                IP address or DNS name of receiver
            port
                Port number to be used at this receiver
            account
                Optional different account number to be used for this path. 
                Most receivers expect a numeric string of 4 to 8 digits
            key
                Optional encryption key.
                This key should be byte string of 16 or 32 bytes                
            receiver
                an optional integer to be used as receiver number in the block header
            line
                an optional integer to be used as line number in the block header
            ptype
                TCP or UDP
        note
            The routing of the back-up path to use the secondary network adapter has to be done
            in the operating system. The decision which adapter to use is made at the moment of routing.
        """
        if account is not None:
            acc = account
            if self.account is None:
                self.account = account
        else:
            acc = self.account
        if receiver is not None:
            rec = receiver
            if self.receiver is None:
                self.receiver = receiver
        else:
            rec = self.receiver
        if line is not None:
            lin = line
            if self.line is None:
                self.line = lin
        else:
            lin = self.line
        self.tpaths_lock.acquire()
        self.tpaths[mb][pb]['path'] = TransPath(host, port, acc, key=key, receiver=rec, line=lin, type=type)
        self.tpaths[mb][pb]['ok'] = 0
        self.tpaths_lock.release()

    def del_path(self, mb, pb):
        """
        Remove a transmission path
        
        parameters
            main/back-up
                value 'main' or 'back-up'
            primary/secondary
                value 'primary' or 'secondary'
        """
        self.tpaths_lock.acquire()
        self.tpaths[mb][pb]['path'] = None
        self.tpaths_lock.release()

    def set_callback(self, cb):
        """
        Set a callback for generated messages

        parameters
            cb
                the function object that gets called when a timeout or restore message is generated
                cb gets called with a msg map
        """
        self.msg_callback = cb

    def get_callback(self):
        """
        returns the callback for generated messages
        """
        return self.msg_callback

    def start_poll(self, main, backup=None, retry_delay=5, ok_msg=None, fail_msg=None):
        """
        Start the automatic polling to the receiver(s)
        
        parameters
            main
                Polling interval of the main path
            backup
                Optional polling interval of the back-up path
            ok_msg  
                Optional map with message to sent on poll restore
            fail_msg
                optional map with message to send when poll fails
        """
        if self.poll is None:
            self.poll = poll_thread(self.account, self.receiver, self.line, self.tpaths, self.tpaths_lock, retry_delay,
                                    self)
            self.poll.set_poll(main, backup, ok_msg, fail_msg)
            self.poll_active = 1
            self.poll.start()
        else:
            self.poll.set_poll(main, backup, ok_msg, fail_msg)

    def stop_poll(self):
        """Stop the automatic polling to the receiver(s)"""
        if self.poll is not None and self.poll.active() == 1:
            self.poll.stop()
            self.poll_active = -1
            self.poll.join()
            self.poll_active = 0
            self.poll = None

    def start_routine(self, rlist):
        if self.poll is None:
            if len(rlist):
                self.poll = poll_thread(self.account, self.receiver, self.line, self.tpaths, self.tpaths_lock, 5.0,
                                        self)
                self.poll.set_routines(rlist)
                self.poll_active = 1
                self.poll.start()
        else:
            self.poll.set_routines(rlist)
            if len(rlist) == 0:
                if self.poll.active() == 2:
                    self.poll.stop()
                    self.poll_active = -1
                    self.poll.join()
                    self.poll_active = 0
                    self.poll = None

    def send_msg(self, mtype, mparam):
        """
        Schedule a message for sending to the receiver
        
        parameters
            mtype
                type of message to send
                current implemented is :
                    'SIA' or 'SIA-DCS' for sending a message with a SIA-DC03 payload
                    'CID' or 'ADM-CID' for sending a message with a SIA-DC05 payload
            mparam
                a map of key value pairs defining the message content.
                for a description of possible values see the documentation of the payload
        
        note
            this method can be called from more than one thread
        """
        msg = ''
        dc09type = ''
        self.counterlock.acquire()
        self.msg_nr += 1
        self.counter += 1
        self.counterlock.release()
        if self.msg_nr > 9999:
            self.msg_nr = 1
        if mtype == 'SIA' or mtype == 'SIA-DCS':
            msg = dc03_msg.dc03event(self.account, mparam)
            dc09type = 'SIA-DCS'
        if mtype == 'CID' or mtype == 'ADM-CID':
            msg = dc05_msg.dc05event(self.account, mparam)
            dc09type = 'ADM-CID'
        extra = dc09_msg.dc09_extra(mparam)
        if extra is not None:
            msg = msg + extra
        tup = self.msg_nr, dc09type, msg
        logging.debug('Message queued nr %s type %s content "%s"', self.msg_nr, dc09type, msg)
        self.queuelock.acquire()
        self.queue.append(tup)
        self.queuelock.release()
        if self.send is not None and self.send.active() == 0:
            self.send.join()
            self.send = None
        if self.send is None:
            self.send = event_thread(self.account, self.receiver, self.line, self.queue, self.queuelock, self.tpaths,
                                     self.tpaths_lock, self)
            self.send.start()

    def state(self):
        """
        Returns a dictionary with current state information

        returns
            dictionary
                msgs queued:
                    number of messages in send queue
                msgs sent:
                    number of messages sent since start
                main primary path ok:
                    true if main primary path is ok
                main secondary path ok:
                    true if main secondary path is ok
                back-up primary path ok:
                    true if back-up primary path is ok
                back-up secondary path ok:
                    true if back-up secondary path is ok
                poll active:
                    true if poll is active
                poll count:
                    number of polls sent since start
                send active:
                    true if at least one message is currently being sent
        """
        ret = {'msgs queued': len(self.queue), 'msgs sent': self.counter}
        for mb in ('main', 'back-up'):
            for ps in ('primary', 'secondary'):
                if self.tpaths[mb][ps]['path'] is not None:
                    ret[mb + ' ' + ps + ' path ok'] = self.tpaths[mb][ps]['ok']
        if self.poll is not None:
            ret['poll active'] = self.poll.active()
            ret['poll count'] = self.poll.count()
        if self.send is not None:
            ret['send active'] = self.send.active()
        return ret

    def isConnected(self):
        """Returns true if there is a connection"""
        antw = False
        for mb in ('main', 'back-up'):
            for ps in ('primary', 'secondary'):
                if self.tpaths[mb][ps]['path'] is not None:
                    if self.tpaths[mb][ps]['ok'] > 0:
                        antw = True
        return antw

    def notSent(self):
        """Returns the number of messages in the send queue"""
        return len(self.queue)

    def transfer_msg(self, msg_nr, mtype, message, path):
        """
        Transfer a message and decode the answer
        if needed repeat with correct time offset
        
        parameters
            msg 
                the message to transfer
            path
                the path to transfer the message over
        return value
            true if message is transferred correct
        """
        ret = False
        dc09 = dc09_msg(path.get_account(), path.get_key(), path.get_receiver(), path.get_line(), path.get_offset())
        mesg = str.encode(dc09.dc09block(msg_nr, mtype, message))
        conn = path.connect()
        if conn is not None:
            antw = conn.sendAndReceive(mesg, 512)
            if antw is not None:
                res = dc09.dc09answer(msg_nr, antw.decode())
                if res is not None:
                    path.set_offset(res[1])
                    if res[0] == 'NAK':
                        dc09.set_offset(res[1])
                        mesg = str.encode(dc09.dc09block(msg_nr, mtype, message))
                        conn.send(mesg)
                        antw = conn.receive(1024)
                        if antw is not None:
                            res = dc09.dc09answer(self.msg_nr, antw)
                    if res[0] == 'ACK':
                        ret = True
            logging.debug('Sent message nr %s mtype %s content %s to %s port %s answer %s', msg_nr, mtype, message,
                          path.host, path.port, antw)
        if conn is not None:
            conn.disconnect()
        return ret


class poll_thread(threading.Thread):
    """
    Handle the polling tasks of SPT (Secured Premises Transciever)
    extra task is handle the routine events if any
    """

    def __init__(self, account, receiver, line, paths, pathlock, retry_delay, parent):
        """
        Create polling thread 
        
        parameters
            account
                account number to use in the poll messages
            receiver
                receiver number to use in poll messages
            line
                line number to use in poll messages
            paths
                dictionary defining the transmission paths to use
            pathlock
                reference to the lock governing the paths dictionary
            retry_delay
                delay in seconds before resend poll message
            parent
                reference to parent class for callback
        """
        threading.Thread.__init__(self)
        self.account = account
        self.receiver = receiver
        self.line = line
        self.tpaths = paths
        self.tpaths_lock = pathlock
        self.parent = parent
        self.poll_retry_delay = retry_delay
        self.main_poll = None
        self.backup_poll = None
        self.routines = []
        self.ok_msg = None
        self.fail_msg = None
        self.main_poll_next = 0
        self.backup_poll_next = 0
        self.main_poll_ok = False
        self.backup_poll_ok = False
        self.counter = 0
        self.routine_nexts = []
        self.running = False
        self.backup_ok = False
        self.main_ok = False

    def set_poll(self, main, backup, ok_msg, fail_msg):
        """
        Set polling parameters

        parameters
            main
                polling interval in seconds of main path(s)
            backup
                polling interval in seconds of back-up path(s)
            ok_msg
                map defining the message to be sent when a path recovers
            fail_msg
                map defining the message to be sent when a path fails
        """
        self.main_poll = main
        self.backup_poll = backup
        self.ok_msg = ok_msg
        self.fail_msg = fail_msg

    def set_routines(self, routines):
        """
        Configure the routine messages

        parameters
            routines
                dictionary with settings for routine messages
                    interval
                        message interval in seconds default is 86400
                    start
                        delay in seconds to first message

        """
        self.routines = routines
        now = time.time()
        for routine in self.routines:
            if 'interval' in routine:
                interval = routine['interval']
            else:
                interval = 86400
            if 'start' in routine:
                start = (now % 86400) + routine['start']
            else:
                start = now
            while start < now:
                start += interval
            self.routine_nexts.append(start)

    # -----------------
    # send polls while needed (call in thread)
    # at first run check all paths
    # ------------------
    def run(self):
        first = True
        while self.main_poll or self.backup_poll or len(self.routines) > 0:
            # on first poll check validity of all paths
            self.running = True
            now = time.time()
            # ---------------
            # main poll 
            # ---------------
            main_polled = False
            back_up_for_main = False
            backup_polled = False
            if self.main_poll is not None and self.main_poll_next <= now:
                for ps in ('primary', 'secondary'):
                    if first or not main_polled:
                        if self.tpaths['main'][ps]['path'] is not None:
                            if self.parent.transfer_msg(0, "NULL", "]", self.tpaths['main'][ps]['path']):
                                main_polled = True
                                self.counter += 1
                                if self.tpaths['main'][ps]['ok'] != 1:
                                    self.tpaths_lock.acquire()
                                    self.tpaths['main'][ps]['ok'] = 1
                                    self.tpaths_lock.release()
                                    self.msg(self.ok_msg, 1, 1)
                            else:
                                if self.tpaths['main'][ps]['ok'] != 0:
                                    self.tpaths_lock.acquire()
                                    self.tpaths['main'][ps]['ok'] = 0
                                    self.tpaths_lock.release()
                                    self.msg(self.fail_msg, 1, 0)
                if not main_polled:
                    self.main_poll_ok = False
                    self.main_ok = False
                    back_up_for_main = True
                else:
                    self.main_poll_ok = True
                    self.main_ok = True
                    self.main_poll_next = now + self.main_poll
            # ---------------
            # backup poll 
            # also triggered when main poll failed 
            # ---------------
            if self.backup_poll is not None and (self.main_poll_next <= now or self.backup_poll_next <= now or first):
                for ps in ('primary', 'secondary'):
                    if first or backup_polled == 0:
                        if self.tpaths['back-up'][ps]['path'] is not None:
                            if self.parent.transfer_msg(0, "NULL", "]", self.tpaths['back-up'][ps]['path']):
                                backup_polled = 1
                                self.counter += 1
                                if self.tpaths['back-up'][ps]['ok'] != 1:
                                    self.tpaths_lock.acquire()
                                    self.tpaths['back-up'][ps]['ok'] = 1
                                    self.tpaths_lock.release()
                                    self.msg(self.ok_msg, 2, 1)
                            else:
                                if self.tpaths['back-up'][ps]['ok'] != 0:
                                    self.tpaths_lock.acquire()
                                    self.tpaths['back-up'][ps]['ok'] = 0
                                    self.tpaths_lock.release()
                                    self.msg(self.fail_msg, 2, 0)
                if not backup_polled:
                    self.backup_poll_ok = False
                    self.backup_ok = False
                else:
                    self.backup_poll_ok = True
                    self.backup_ok = True
                    self.backup_poll_next = now + self.backup_poll
            if self.main_poll is not None and main_polled and (self.backup_poll is None or backup_polled):
                first = False
            # -----------------
            # schedule retry of main
            # -----------------
            if main_polled or (back_up_for_main and backup_polled):
                if self.main_poll is not None and self.main_poll_next < now:
                    self.main_poll_next = now + self.main_poll
            # ------------------------------
            # handle routine messages
            # -----------------------------
            if len(self.routines) > 0:
                self.do_routines()
            # -------------------------
            # decide how long to sleep
            # -------------------------
            time.sleep(self.poll_retry_delay)

    def msg(self, msg, ps, ok):
        """
        Send a message on poll state change
        """
        if msg is not None:
            nmsg = msg
            nmsg['zone'] = ps
            mtype = None
            if 'type' in msg:
                mtype = msg['type']
            else:
                if 'code' in msg:
                    code = msg['code']
                    if len(code) == 3:
                        mtype = 'ADM-CID'
                        if ok:
                            nmsg['q'] = 1
                        else:
                            nmsg['q'] = 3
                    elif len(code) == 2:
                        mtype = 'SIA-DCS'
            if mtype is not None:
                self.parent.send_msg(mtype, msg)
                if self.parent.get_callback() is not None:
                    self.parent.get_callback()(mtype, msg)

    def stop(self):
        self.main_poll = None
        self.backup_poll = None
        self.routines = []

    def active(self):
        ret = 0
        if self.main_poll or self.backup_poll:
            ret += 1
        if len(self.routines) > 0:
            ret += 2
        return ret

    def count(self):
        return self.counter

    def do_routines(self):
        now = time.time()
        cnt = 0
        for n, r in zip(self.routine_nexts, self.routines):
            if n <= now:
                if 'type' in r:
                    mtype = r['type']
                else:
                    if 'code' in r:
                        code = r['code']
                        if len(code) == 3:
                            mtype = 'ADM-CID'
                        else:
                            mtype = 'SIA-DCS'
                    else:
                        mtype = 'SIA-DCS'
                self.parent.send_msg(mtype, r)
                if 'interval' in r:
                    interval = r['interval']
                else:
                    interval = 86400
                self.routine_nexts[cnt] = now + interval
            cnt += 1


class event_thread(threading.Thread):
    """
    Handle the transmitting of events of SPT (Secured Premises Transciever)
    """

    def __init__(self, account, receiver, line, queue, queuelock, tpaths, tpaths_lock, parent):
        """
        Handle the Transmitting of events as defined in 
            SIA DC09 specification
            EN 50136-1
        
        parameters
            account
                Account number to be used. 
                Most receivers expect a numeric string of 4 to 8 digits
            receiver
                an optional integer to be used as receiver number in the block header
            line
                an optional integer to be used as line number in the block header
        """
        threading.Thread.__init__(self)
        self.account = account
        self.receiver = receiver
        self.line = line
        self.queue = queue
        self.queuelock = queuelock
        self.tpaths = tpaths
        self.tpaths_lock = tpaths_lock
        self.send_retry_delay = 0.5
        self.parent = parent
        self.running = False

    # -----------------
    # send events while needed (call in thread)
    # checks message queue and retries
    # ------------------
    def run(self):
        while len(self.queue) > 0:
            # --------------------
            # first handle queue
            # --------------------
            self.running = True
            sent = 1
            while sent and len(self.queue):
                sent = self.send()
                #            now = time.time()
                # -------------------------
                # decide how long to sleep
                # -------------------------
                #            if self.main_poll_next < self.backup_poll_next:
                #                next = self.main_poll_next
                #            else:
                #                next = self.backup_poll_next
                #            if next > now:
                if len(self.queue):
                    time.sleep(self.send_retry_delay)
        self.running = False

    def send(self):
        self.queuelock.acquire()
        if len(self.queue) == 0:
            self.queuelock.release()
            return
        mess = self.queue.popleft()
        self.queuelock.release()
        msg_sent = False
        # ---------------------------
        # first try known good paths
        # --------------------------
        for mb in ('main', 'back-up'):
            for ps in ('primary', 'secondary'):
                if msg_sent == 0 and self.tpaths[mb][ps]['path'] is not None:
                    if self.tpaths[mb][ps]['ok']:
                        if self.parent.transfer_msg(mess[0], mess[1], mess[2], self.tpaths[mb][ps]['path']):
                            msg_sent = True
        # ---------------------------
        # then try all available paths
        # --------------------------
        if not msg_sent:
            for mb in ('main', 'back-up'):
                for ps in ('primary', 'secondary'):
                    if not msg_sent and self.tpaths[mb][ps]['path'] is not None:
                        if self.parent.transfer_msg(mess[0], mess[1], mess[2], self.tpaths[mb][ps]['path']):
                            msg_sent = True
                            self.tpaths_lock.acquire()
                            self.tpaths[mb][ps]['ok'] = 1
                            self.tpaths_lock.release()
        if not msg_sent:
            self.queuelock.acquire()
            tup = mess[0], mess[1], mess[2]
            self.queue.appendleft(tup)
            self.queuelock.release()
        return msg_sent

    def active(self):
        return self.running
