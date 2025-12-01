import zmq
import constWC

context = zmq.Context()

receiver = context.socket(zmq.PULL)
receiver.connect("tcp://" + constWC.HOST + ":" + constWC.PORT_SPLITTER)

sender1 = context.socket(zmq.PUSH)
sender1.connect("tcp://" + constWC.HOST + ":" + constWC.PORT_RED1)

sender2 = context.socket(zmq.PUSH)
sender2.connect("tcp://" + constWC.HOST + ":" + constWC.PORT_RED2)

print("Mapper gestartet")

while True:
    sentence = receiver.recv_string()
    
    # Wenn das Signal kommt: Weiterleiten an BEIDE Reducer
    if sentence == "STOP":
        sender1.send_string("STOP")
        sender2.send_string("STOP")
        continue

    # Normale Arbeit
    print(f"Verarbeite: {sentence}")
    words = sentence.replace(",", "").replace(".", "").split()
    
    for word in words:
        if word[0].lower() < 'm':
            sender1.send_string(word)
        else:
            sender2.send_string(word)
            