from multiprocessing.connection import Listener, Client
import multiprocessing
import threading
import os
from random import randint
# in this implementation, we're assuming the mobile station at address 5000 is already connected the nearest
# eNb tower at address 5001 and we're continuing the attach process from here starting with the UE sending an attach
# request

# current dummy sequence (still not complete)
# 1- ue sends attach request to enb
# 2- enb forwards the request to mme
# 3- mme forwards the request to sgw
# 4- sgw replies 'accept' and sends it to the mme
# 5- mme sends the accept to the enb


port_addresses = {'UE': 5000, 'eNb': 5001, 'MME': 5003, 'HSS': 5004, 'PGW': 5005, 'SGW': 5006}

def generate_random_ip():
    return ".".join(map(str, (randint(0, 255)
                       for _ in range(4))))

class LteProcess:
    def __init__(self, my_port):
        self.my_port = my_port


    def listen(self):
        address = ('localhost', self.my_port)
        listener = Listener(address)
        while True:
            conn = listener.accept()
            # print(self.__class__.__name__, ' has connection from', listener.last_accepted)
            while True:
                msg = conn.recv()
                # do something with msg
                if msg != 'close':
                    print(self.__class__.__name__, ' has a message received:  ', msg)
                self.handle_incoming_message(msg, conn)
                if msg == 'close':
                    conn.close()
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
        # self.target_port = port_addresses['eNb']

    def attach(self, eNb_address=port_addresses['eNb']):
        attach_request = f'ATTACH REQUEST FROM UE AT ADDRESS|{self.my_port}-IMSI={self.IMSI}'
        listener_thread = threading.Thread(target=self.listen)
        communicator_thread = threading.Thread(target=self.talk, args=(eNb_address, attach_request))
        listener_thread.start()
        communicator_thread.start()

    def handle_incoming_message(self, msg, conn):
        if msg == 'CONNECTION ACCEPTED':
            print('UE: connection was accepted')


class eNb(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['eNb'])

        # self.communicator_thread.start()
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def handle_incoming_message(self, msg, conn):
        if msg.split()[:2] == ['ATTACH', 'REQUEST']:
            # forward msg to mme
            self.communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], msg))
            self.communicator_thread.start()
        if msg.split()[:2] == ['CONNECTION', 'ACCEPTED']:
            self.communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['UE'], msg))
            self.communicator_thread.start()



class MME(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['MME'])

        # self.communicator_thread.start()
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def handle_incoming_message(self, msg, conn):
        # do something when receiving a message
        # you might want to start a communicator thread (look at enb for reference)
        # and send something to the hss
        # send to the SGW something that starts with 'CREATE SESSION'

        #do authentication logic

        if msg.split()[:2] == ['ATTACH', 'REQUEST']:
            self.communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['SGW'], 'CREATE SESSION'))
            self.communicator_thread.start()

        if msg.split()[:2] == ['CONNECTION', 'ACCEPTED']:
            self.communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['eNb'], msg))
            self.communicator_thread.start()





class HSS(LteProcess):
    # self.communicator_thread.start()
    def __init__(self):
        super().__init__(port_addresses['HSS'])

        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()


    def handle_incoming_message(self, msg, conn):
        # do something when receiving a message
        # you might want to start a communicator thread (look at enb for reference)
        # and send something to the hss
        pass


class SGW(LteProcess):
    def __init__(self):
        super().__init__(port_addresses['SGW'])

        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def handle_incoming_message(self, msg, conn):

        if msg.split()[:2] == ['CREATE', 'SESSION']:
            response = 'CONNECTION ACCEPTED. SESSION CREATED'
            self.communicator_thread = threading.Thread(target=self.talk, args=(port_addresses['MME'], response))
            self.communicator_thread.start()



class PGW(LteProcess):
    pass


if __name__ == '__main__':
    enb1 = eNb()

    UE1 = UE()
    mme = MME()
    sgw = SGW()

    UE1.attach()
