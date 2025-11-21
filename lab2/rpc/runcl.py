import rpc
import logging
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

# Callback-Funktion zur Verarbeitung des Ergebnisses
def result_callback(result):
    print("Hallo hier Callback <3")
    print("Result: {}".format(result.value))

cl = rpc.Client()
cl.run()

#von Foo Bar auf Goodbye World geändert
base_list = rpc.DBList({'Goodbye'})
result_list = cl.append('World', base_list, result_callback)

for i in range(15):
            print(f"Warte auf Antwort... {i+1}/15")
            time.sleep(1)
#thread.join()  # warte bis thread fertig ist

cl.stop()


#Original ohne Callback
#lab_logging.setup(stream_level=logging.INFO)

#cl = rpc.Client()
#cl.run()

#base_list = rpc.DBList({'foo'})
#result_list = cl.append('bar', base_list)

#print("Result: {}".format(result_list.value))

#cl.stop()
