import time
from multiprocessing.connection import Listener, Client
import multiprocessing
import threading
import os
from random import randint
from time import sleep
from helpers import *

# in this implementation, we're assuming the mobile station at address 5000 is already connected the nearest
# eNb tower at address 5001 and we're continuing the attach process from here starting with the UE sending an attach
# request

stop_listening_after_attach = False

port_addresses = {'UE': 5000, 'eNb': 5001, 'MME': 5003, 'HSS': 5004, 'PGW': 5005, 'SGW': 5006}


class LteProcess:
    def __init__(self, my_port):
        self.my_port = my_port

    def stop_all(self):
        try:
            self.talk(port_addresses['eNb'], 'STOP LISTENING')
        except:
            pass
        try:
            self.talk(port_addresses['MME'], 'STOP LISTENING')
        except:
            pass
        try:
            self.talk(port_addresses['HSS'], 'STOP LISTENING')
        except:
            pass

        try:
            self.talk(port_addresses['SGW'], 'STOP LISTENING')
        except:
            pass
        try:
            self.talk(port_addresses['PGW'], 'STOP LISTENING')
        except:
            pass

        try:
            self.talk(port_addresses['UE'], 'STOP LISTENING')
        except:
            pass

    def listen(self):
        address = ('localhost', self.my_port)
        listener = Listener(address)
        # timeout = time.time() + 10
        while True:
            conn = listener.accept()
            # print(self.__class__.__name__, ' has connection from', listener.last_accepted)
            while True:
                msg = conn.recv()
                # do something with msg
                if msg != 'close':
                    print(self.__class__.__name__, ' has a message received:  ', msg, '\n')

                self.handle_incoming_message(msg, conn)

                if msg in ['close', 'STOP LISTENING']:
                    conn.close()
                    break

            if msg == 'STOP LISTENING':
                break

        listener.close()

    def talk(self, target_address, msg):
        if not target_address:
            return
        try:
            iter(target_address)
        except:
            target_address = ('localhost', target_address)

        conn = Client(target_address)
        if type(msg) != list():
            msg = [msg]
        for m in msg:
            conn.send(m)
        conn.send('close')
        conn.close()

    def handle_incoming_message(self, msg, conn):
        pass


class UE(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['UE'])
        self.IMSI = randint(100000000000, 999999999999)
        self.MEI = randint(100000000000, 999999999999)  # mobile equipment identity
        # self.target_port = port_addresses['eNb']
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()
        # self.listener_thread.join()

    def attach(self, eNb_address=port_addresses['eNb']):
        print('********starting the attach procedure********\n\n')
        attach_request = f'ATTACH REQUEST FROM UE AT ADDRESS|{self.my_port}-IMSI={self.IMSI}|-MEI={self.MEI}'
        communicator_thread = threading.Thread(target=self.talk, args=(eNb_address, attach_request))
        communicator_thread.start()
        # communicator_thread.join()
        
        
    def detach(self, eNb_address=port_addresses['MME']):
        print('\n\n ********starting the detach procedure********\n\n')

        attach_request = f'DETACH REQUEST'
        communicator_thread = threading.Thread(target=self.talk, args=(eNb_address, attach_request))
        communicator_thread.start() 

    def handle_incoming_message(self, msg, conn):
        if msg.split()[:3] == ['USER', 'AUTHENTICATION', 'TOKEN']:
            reply = f'UE AUTHENTICATION TOKEN={Authentication_token(self.IMSI)}'
            communicator_thread = threading.Thread(target=self.talk,
                                                   args=(port_addresses['MME'], reply))
            communicator_thread.start()

        if msg == 'ATTACH ACCEPT':
            print('UE: connection was accepted')

        elif msg == 'RRC RECONFIGURATION':
            sleep(0.005)
            msg = "ATTACH COMPLETE"
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], msg))
            communicator_thread.start()            


class eNb(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['eNb'])

        # self.communicator_thread.start()
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()
        # self.listener_thread.join()

    def handle_incoming_message(self, msg, conn):

        if msg.split()[:2] == ['ATTACH', 'REQUEST']:
            ms, meta,MEI = msg.split('|')
            in_port, IMSI = meta.split('-IMSI=')
            MEI = int(MEI.split('-MEI=')[1])
            msg = f'ATTACH REQUEST FROM eNb AT ADDRESS|{self.my_port}-IMSI={IMSI}|-MEI={MEI}'
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], msg))
            communicator_thread.start()

        elif msg.split()[:2] == ['ATTACH', 'ACCEPT']:
            attach_accept, context = msg.split('/')
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['UE'], attach_accept))
            communicator_thread.start()
            response = "RRC RECONFIGURATION"
            communicator_thread2 = threading.Thread(target=self.talk, args=(port_addresses['UE'], response))
            communicator_thread2.start()            
            # communicator_thread2.join()
            context_response = "INITAL CONTEXT SETUP RESPONSE"
            communicator_thread3 = threading.Thread(target=self.talk, args=(port_addresses['MME'], context_response))
            communicator_thread3.start()  
        elif msg == "UE CONTEXT RELEASE COMMAND":
            
            communicator_thread = threading.Thread(target=self.talk,args=(port_addresses['MME'],"UE CONTEXT RELEASE COMPLETE"))
            communicator_thread.start()            
            
            
class MME(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['MME'])
        # self.communicator_thread.start()
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()
        # self.listener_thread.join()
        
    def handle_incoming_message(self, msg, conn):
        # do something when receiving a message
        # you might want to start a communicator thread (look at enb for reference)
        # and send something to the hss
        # send to the SGW something that starts with 'CREATE SESSION'

        # do authentication logic

        if msg.split()[:2] == ['ATTACH', 'REQUEST']:
            ms, meta,MEI = msg.split('|')
            in_port, IMSI = meta.split('-IMSI=')
            self.MEI = int(MEI.split('-MEI=')[1])
            self.IMSI = int(IMSI)

            authentication_request = f'USER AUTHENTICATION REQUEST FROM MME AT ADDRESS|{self.my_port}-IMSI={self.IMSI}'
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['HSS'], authentication_request))
            communicator_thread.start()

        elif msg.split()[:3] == ['HSS', 'REFERENCE', 'AUTHENTICATION']:
            _, self.REF_TOKEN = msg.split('=')
            authentication_request = f'USER AUTHENTICATION TOKEN REQUEST FROM MME AT ADDRESS|{self.my_port}'
            communicator_thread = threading.Thread(target=self.talk,
                                                   args=(port_addresses['UE'], authentication_request))
            communicator_thread.start()

        elif msg.split()[:2] == ['UE', 'AUTHENTICATION']:
            _, user_token = msg.split('=')
            if user_token == self.REF_TOKEN:
                print('AUTHENTICATION SUCCESSFUL\n')
                request = f'UPDATE LOCATION REQUEST FROM MME AT ADDRESS|{self.my_port}-IMSI={self.IMSI}'
                communicator_thread = threading.Thread(target=self.talk,
                                                       args=(port_addresses['HSS'], request))
                communicator_thread.start()

        elif msg.split()[:3] == ['UPDATE', 'LOCATION', 'ACKNOWLEDGEMENT']:
            session_request = f'CREATE SESSION REQUEST FROM MME AT ADDRESS|{self.my_port}-IMSI={self.IMSI}|-MEI={self.MEI}'
            communicator_thread = threading.Thread(target = self.talk, args =(port_addresses['SGW'], session_request))
            communicator_thread.start()
            
        elif msg.split()[:3] == ['CREATE', 'SESSION', 'RESPONSE']:
            response = "ATTACH ACCEPT / INITAL CONTEXT SETUP REQUEST"
            communicator_thread2 = threading.Thread(target=self.talk, args=(port_addresses['eNb'], response))
            communicator_thread2.start()
        elif msg == "ATTACH COMPLETE":
            bearer_request = "MODIFY BEARER REQUEST"
            communicator_thread = threading.Thread(target = self.talk, args =(port_addresses['SGW'], bearer_request))
            communicator_thread.start()            
     
        elif msg == "MODIFY BEARER RESPONSE":
            print("mme: Attach procedures done!")
            if stop_listening_after_attach:
                stopper_thread = threading.Thread(target=self.stop_all)
                stopper_thread.start()
            

        elif msg == 'DETACH REQUEST':
    
            delete_request = 'DELETE SESSION REQUEST'
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['SGW'], delete_request))
            communicator_thread.start()

        elif msg == "DELETE SESSION RESPONSE":
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['UE'], "DETACH ACCEPT"))
            communicator_thread.start()
            
            communicator_thread2 = threading.Thread(target=self.talk,args=(port_addresses['eNb'],"UE CONTEXT RELEASE COMMAND"))
            communicator_thread2.start()            
        elif msg == "UE CONTEXT RELEASE COMPLETE":
            print("mme: Detach procedures done!")
            stopper_thread = threading.Thread(target=self.stop_all)
            stopper_thread.start()
            
            
class HSS(LteProcess):
    # self.communicator_thread.start()
    def __init__(self):
        super().__init__(port_addresses['HSS'])

        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()
        # self.listener_thread.join()

    def handle_incoming_message(self, msg, conn):
        # do something when receiving a message
        # you might want to start a communicator thread (look at enb for reference)
        # and send something to the hss
            
        if msg.split()[:3] == ['USER', 'AUTHENTICATION', 'REQUEST']:
                ms, meta = msg.split('|')
                in_port, IMSI = meta.split('-IMSI=')
                self.IMSI = int(IMSI)
                response = f'HSS REFERENCE AUTHENTICATION TOKEN={Authentication_token(self.IMSI)}'
                communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], response))
                communicator_thread.start()

        if msg.split()[:3] == ['UPDATE', 'LOCATION', 'REQUEST']:
                ms, meta = msg.split('|')
                in_port, IMSI = meta.split('-IMSI=')
                self.IMSI = int(IMSI)
                response = 'UPDATE LOCATION ACKNOWLEDGEMENT'
                communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], response))
                communicator_thread.start()


class SGW(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['SGW'])

        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()
        # self.listener_thread.join()

    def handle_incoming_message(self, msg, conn):
        if type(msg) != str:
            msg = GTP_c_decapsulate(msg)

        if msg.split()[:3] == ['CREATE', 'SESSION', 'REQUEST']:
            ms, meta, MEI = msg.split('|')
            in_port, IMSI  = meta.split('-IMSI=')
            self.current_MEI= int(MEI.split('-MEI=')[1])
            self.current_IMSI = int(IMSI)
            session_request = f'CREATE SESSION REQUEST FROM SGW AT ADDRESS|{self.my_port}-IMSI={self.current_IMSI}|-MEI={self.current_MEI}'
            session_request = GTP_c_encapsulate(session_request, imsi=self.current_IMSI, mei=self.current_MEI)
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['PGW'], session_request))
            communicator_thread.start()
            # communicator_thread.join()
        elif msg.split()[:3] == ['CREATE', 'SESSION', 'RESPONSE']:
            communicator_thread2 = threading.Thread(target=self.talk, args=(port_addresses['MME'], msg))
            communicator_thread2.start()
            # communicator_thread2.join()
        elif msg == "MODIFY BEARER REQUEST":
            bearer_response = "MODIFY BEARER RESPONSE"
            communicator_thread = threading.Thread(target = self.talk, args =(port_addresses['MME'], bearer_response))
            communicator_thread.start()   
        elif msg == "DELETE SESSION REQUEST":
            delete_response = "DELETE SESSION RESPONSE"
            communicator_thread = threading.Thread(target = self.talk, args =(port_addresses['MME'], delete_response))
            communicator_thread.start()             


class PGW(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['PGW'])

        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def handle_incoming_message(self, msg, conn):
        if type(msg) != str:
            msg = GTP_c_decapsulate(msg)

        if msg.split()[:3] == ['CREATE', 'SESSION', 'REQUEST']:
            self.IMSI, self.MEI =[int(i) for i in msg.split('-IMSI=')[1].split('|-MEI=')]

            response = 'CREATE SESSION RESPONSE'
            response = GTP_c_encapsulate(response, self.IMSI, self.MEI)
            communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['SGW'], response))
            communicator_thread.start()
            # communicator_thread.join()



