# dc09_spt (Secure Premises Transceiver a.k.a. dialler)
A set of python classes to implement a dialler using the SIA-DC09 protocol set and conforming to the EN-50136-1 norm

The provided classes should be enough to implement an dialler (SPT, Secure Premises Transceiver, in EN-50136-1 lingo) with the following functions
  
## What functions are implemented
Implemented functions as for now are :
* construction of messages according to the SIA-DC09 standard
* construction of the payload events for SIA-DC09 according to the SIA-DC07 standard
* construction of the payload events for SIA-DC07 according to the SIA-DC03 standard
* construction of the payload events for SIA-DC07 according to the SIA-DC05 standard
* crypt the SIA-DC09 messages using AES128 or AES256
* poll main and optionally back-up transmission paths according to EN 50136-1 norm in a separate thread
* use of primary paths for both the main and the back-up transmission paths resulting in a total of 4 paths per dialler
* transmission of DC09 events efficiently in a separate thread and check the answer before deleting them from the queue
* send timed routine messages
* keep track of time offset of the various receivers.

## Introduction
As a developer of security software i often heard the complaint that it would be hard to write a decent protocol implementation, especially when checksums and encryption are involved. While being one of the authors of a multi protocol IP receiver i did not have the feel that it would be too hard.

Then, when a friend asked if i knew an example of the SIA-DC09 protocol in the Internet to be used as a reference for development, and i could not find any, combined with him mentioning python and my long standing wish to try that language too, it started itching.
And the next weekend i started learning python (not that difficult after many years programming many languages) and made a set of classes to handle the DC09 messages.

While testing these classes in the evenings of the next week, and getting fun further exploring the possibilities of python, i added this dc09_dialler class for testing the protocol, and noticed it could be interesting for others to use or read this software.

Because our company is not in the business of making transmitters, but specialized in making redundant multi protocol receivers and Alarm Monitoring Software, we decided to open source this set of classes.

The provided example (command line) application, creates two independant diallers with both their polling and routine messages and a simple way to send events. The hosts mentioned in the example are our test receivers. You are encouraged to try sending events to them.

Please remember i am an C/C++ programmer and this is my first venture into an python module. It is very likely that serious python programmers have many hints and remarks at my code. Please comment or correct. Learning python was the main reason to start this project.

# Protocol basics
The SIA-DC09 protocol definition defines how to send optionally encrypted events to a receiver and perform the transmission path tests by sending poll messages.
The events sent in such an DC09 block is defined in the SIA-DC07 standard.

This DC07 standard is basically a description how an receiver can communicate with AMS (Alarm Monitoring Station) software and can transfer messages in various transmitter protocols.

This set of classes implements the SIA-DC03 (a.k.a. "SIA") and the SIA-DC05 (a.k.a. "CID") transmitter protocols. These two protocols make up for well over 90% of the used message formats in alarm messaging. In effect it should be possible to cover most use cases.

## Dialler configuration
In general the configuration consists of defining account number, encryption key and communication paths.

### instantiating a dialler
At instantiating a dialler, you specify the account number to be used for the envelope. That, together with the receiver and line number, defines the SPT in the protocol.

example : 
```
spt = dc09_spt("0123")
```

### define a communication path
Next you define the communication paths to be used to reach the receiver and the encrytion key to be used in that path.

example : 
```
spt.set_path("main", "primary", "ovost.eu", 12128, "0123", key=None)
```

Each spt can handle 4 paths, labeled main.primary, main.secondary, back-up.primary and back-up.secondary.
The main path is for the main transmission path, where the fast poll message will be sent.
Main.primary connects to the primary receiver, main.secondary to the secondary receiver.
The back-up path will only be used if the main path is unavailable except for the slow poll to show its availability.

### set the polling frequency and messages for fail and restore
Polling is defined in SIA-DC09 to show the communication path is available for transfer of events. The polling interval is, for Europe, defined in the EN-50136-1 norm.
For dual path the polling in the back-up path will take over the frequency of the main path in case it fails.

example :
```
spt.start_poll(85,890, ok_msg={'code':  'YK'},  fail_msg={'code':  'YS'})
```

### optionally set routine reports
Normally it is preferred that the alarm panel, in this case the application using this set of classes sends the routine events to show it is functioning, but it can be delegated to the dc09_spt class by defining a routine report.
I suggest to use a zone number of 99 in SIA and 999 in CID type messages to make it possible to recognize the SPT originated messages.

example:
```
spt.start_routine([{'interval':  7200,  'type': 'SIA-DCS',  'code':  'RP',  'zone':  99}])
```

## Send an event
To send an event you call the send_msg method with the type of message and an map with the content. In the message you can define a different account number if the receiver accepts that.

example:
```
spt.send_msg('SIA-DCS', {'code':'OP','zone': 14,  'time':  'now'})
spt.send_msg('ADM-CID', {'account':  '124',  'code': 400, 'q': 1, 'zone': 14})
```

# Next steps
This is the first upload of these classes. In my tests they work, but some work is still planned for the near future:

## To Do
~~1. complete the package for upload to Pipi~~
2. extend documentation and comments
3. extend the dc03_msg class to handle all keys defined in the DC03 standard. (this subset should be enough for over 90% of the use cases though)
4. extend the dc09_msg class with the extensions of the SIA-DC09 2013 version




