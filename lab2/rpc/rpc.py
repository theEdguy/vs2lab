import constRPC
from context import lab_channel

from time import sleep # ede hier -> für sleep
import threading  # ede hier -> für thread



class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server

        #ede hier -> logic verändern -> ack empfangen ->
        #dan tread erstellen der wartet auf reply
        #rest macht jede sekunde einfach ein print mit zähler
        
        #hilffunktion um wert in variable zu speichern
        msgrcv = [None]
        def wait_for_response():
            nonlocal msgrcv 
            msgrcv= self.chan.receive_from(self.server)
        
        ack_received = False
        while not ack_received:
            print("Warte für ACK...")
            ACK_Check = self.chan.receive_from(self.server, timeout=5)
            if ACK_Check[1][0] == "ACK":
                ack_received = True
                print("ACK da! -> Thread für Antwort wartet...")

                thread = threading.Thread(target=wait_for_response)
                thread.start()
            else:
                print("Warte weiter auf ACK...")

        #client macht anderes
        for i in range(10):
            print(f"Warte auf Antwort... {i+1}/10")
            sleep(1)

        # backup von originalcode -> msgrcv = self.chan.receive_from(self.server)
        # wait for response
        return msgrcv[1]  # pass it to caller


class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters

                #ede hier -> ack senden und dan sleep
                self.chan.send_to(client, ("ACK",))
                sleep(10) 
                #
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, result)  # return response
                else:
                    pass  # unsupported request, simply ignore
