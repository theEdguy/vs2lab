import zmq
import sys
import constWC

if len(sys.argv) > 1:
    red_id = sys.argv[1]
else:
    print("Bitte ID angeben: python reducer.py 1")
    sys.exit()

context = zmq.Context()
receiver = context.socket(zmq.PULL)

if red_id == "1":
    port = constWC.PORT_RED1
elif red_id == "2":
    port = constWC.PORT_RED2
else:
    sys.exit()

receiver.bind("tcp://*:" + port)
print(f"Reducer {red_id} läuft auf Port {port}...")

counts = {}
signals_received = 0
EXPECTED_MAPPERS = 3 #3 Mapper -> alle müssen ein Stop Signal senden, dann sind wir fertig

while True:
    word = receiver.recv_string()
    
    if word == "STOP":
        signals_received += 1
        # Prüfen, ob alle Mapper das STOP Signal gesendet haben
        if signals_received == EXPECTED_MAPPERS:
            # --- Endstand AUSGEBEN ---
            print("\n" + "="*30)
            print(f" ERGEBNIS {red_id}")
            print("="*30)
            for w in sorted(counts.keys()):
                print(f"{w}: {counts[w]}")
            print("="*30 + "\n")
            
            # Reset für den nächsten Lauf (falls man Splitter nochmal startet)
            signals_received = 0
            # Hinweis: 'counts' wird NICHT gelöscht, wir zählen einfach weiter hoch.
            
            # Wordcount resetten
            signals_received = 0
            counts = {}  # <--- HIER LÖSCHEN WIR DIE ALTEN DATEN
    else:
        # Wörter Zählen
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1
        print(f"Update: {word} -> {counts[word]}")
        