import zmq
import time
import random
import constWC

context = zmq.Context()
sender = context.socket(zmq.PUSH)
address = "tcp://*:" + constWC.PORT_SPLITTER
sender.bind(address)

#damit alle Zeit für den Verbindungsaufbau haben
time.sleep(0.5)

sentences = [
    "Nach dem Spiel ist vor dem Spiel",
    "Der Ball ist rund",
    "Verteilte Systeme zwei ist super",
    "Fischers Fritze fischt frische Fische",
    "Zehn zahme Ziegen zogen zehn Zentner Zucker zum Zoo.",
    "Einer für alle, alle für einen",
    "Wenn Fliegen hinter Fliegen fliegen, fliegen Fliegen Fliegen nach.",
    "Ende gut, alles gut"
]

print("--- Start der Datenübertragung ---")

for sentence in sentences:
    #sentence = random.choice(sentences)
    print(f"Sende: {sentence}")
    sender.send_string(sentence)
    time.sleep(0.1)

print("--- Daten fertig. Sende STOP Signal ---")
#for _ in range(3):
sender.send_string("STOP")

# Der Splitter beendet sich
# aber Mapper und Reducer bleiben wach für den nächsten Splitter-Lauf.
print("Splitter beendet")
