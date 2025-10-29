"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    #logge alle Interaktionen
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #erstelle Socket mit IPv4 Adresse und TCP
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT)) #Socket gehört der Adresse die in const_cs.py
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))
        self.phonebook = { #kann man sich vorstellen wie eine Datenbank um Namen nachzuschlagen
            "Alice": "12345",
            "Bob": "67890",
            "Charlie": "54321"
        }

    def serve(self):
        """ Serve echo """
        self.sock.listen(1) #wartet darauf, kontaktiert zu werden
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                self._logger.info(f"Connected by {address}")
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    msg = data.decode("ascii")
                    if msg.startswith("GET:"): #prüfe,ob Nachricht mit GET anfängt
                        name = msg[4:] #hole dir den namen (ab 4. Zeichen der Nachricht)
                        if name in self.phonebook: #schau in der "Datenbank" nach, ob der Name existiert
                            response = f"{name}:{self.phonebook[name]}\n" #Baue die Antwort
                            connection.sendall(response.encode('ascii')) #schicke Antwort an Client
                        else:
                            response = "ERROR:WrongName\n" #falls der Name nicht gefunden wurde, schicke Error an den Client
                            connection.sendall(response.encode('ascii'))
                    elif msg == "GETALL": #prüfe, ob Nachricht mit GETALL anfängt
                        response = "".join([f"{n}:{num}\n" for n, num in self.phonebook.items()]) #erstelle langen String mit allen Einträgen aus der "Datenbank" (Namen durch \n getrennt)
                        connection.sendall(response.encode('ascii')) #schicke Antwort
                    else:
                        connection.sendall(b"ERROR:UnknownCommand\n") #falls weder GET noch GETALL erkannt, schicke Error an Client, dass Command nicht erkannt wurde
                        connection.close()
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")

    def close(self): #definiere Methode um den Server zu schließen (eigentlich nur da um Schreibarbeit zu sparen)
        self.sock.close()


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #erstelle Stocket mit IPv4 und TCP
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, msg_in="Hello, world"):
        """ Call server """
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out
    
    def GET(self, name):
        string = "GET:" + name #erstelle String mit GET und dem angefragten Namen dahinter (Protokollnachricht)
        self.sock.send(string.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii').strip() #dekodiere Antwort und entferne das \n dahinter (wichtig für die Tests später da sonst der Vergleich failed!!)
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out
    
    def GETALL(self, msg_in="GETALL"):
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii').strip()
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out

    def close(self):
        """ Close socket """
        self.sock.close()
