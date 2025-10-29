import unittest
import threading
import time
import clientserver  # Stellt sicher, dass clientserver.py im selben Ordner ist
import logging

# Logging für die Tests aktivieren
clientserver.lab_logging.setup(stream_level=logging.INFO)

class TestPhonebook(unittest.TestCase):
    
    server_thread = None
    server = None

    @classmethod
    def setUpClass(cls):
        # Server in einem eigenen Thread starten
        cls.server = clientserver.Server()
        cls.server_thread = threading.Thread(target=cls.server.serve)
        cls.server_thread.daemon = True # Thread beendet sich, wenn Hauptprogramm endet
        cls.server_thread.start()
        time.sleep(0.5) # Kurz warten, bis der Server bereit ist

    @classmethod
    def tearDownClass(cls):
        """ STOPPT den Server, nachdem alle Tests gelaufen sind """
        logging.info("=== Stoppe Server nach Tests ===")
        cls.server.close() # Signalisiert der 'serve'-Schleife zu stoppen
        cls.server_thread.join(timeout=1.0) # Wartet kurz, bis der Thread sich beendet
        logging.info("=== Server gestoppt ===")

        
    def test_01_get_success(self):
        """ Testet eine erfolgreiche GET-Anfrage """
        logging.info("Starte test_01_get_success")
        client = clientserver.Client() # Neuer Client für jeden Test
        result = client.GET("Bob")
        self.assertEqual(result, "Bob:67890")

    def test_02_get_fail(self):
        """ Testet eine fehlschlagende GET-Anfrage (falscher Name) """
        logging.info("Starte test_02_get_fail")
        client = clientserver.Client()
        result = client.GET("David")
        self.assertEqual(result, "ERROR:WrongName")

    def test_03_get_all(self):
        """ Testet die GETALL-Anfrage """
        logging.info("Starte test_03_get_all")
        client = clientserver.Client()
        result = client.GETALL()
        # Prüfen, ob alle Namen aus dem Telefonbuch in der Antwort enthalten sind
        self.assertIn("Alice:12345", result)
        self.assertIn("Bob:67890", result)
        self.assertIn("Charlie:54321", result)

    def test_04_unknown_command(self):
        """ Testet ein unbekanntes Kommando """
        logging.info("Starte test_04_unknown_command")
        client = clientserver.Client()
        # Wir müssen die API umgehen, um ein ungültiges Kommando zu senden
        client.sock.send(b"DELETE:Alice") 
        data = client.sock.recv(1024)
        result = data.decode('ascii').strip()
        client.close()
        self.assertEqual(result, "ERROR:UnknownCommand")

if __name__ == '__main__':
    unittest.main()