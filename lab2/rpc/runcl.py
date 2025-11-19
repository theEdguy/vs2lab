import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

# Callback-Funktion zur Verarbeitung des Ergebnisses
def result_callback(result):
    print("Hallo hier Callback <3")
    print("Result: {}".format(result.value))

cl = rpc.Client()
cl.run()

# Ede hier von Foo Bar auf Goodbye World geändert
base_list = rpc.DBList({'Goodbye'})
result_list = cl.append('World', base_list, result_callback)

cl.stop()


#Original ohne Callback
#lab_logging.setup(stream_level=logging.INFO)

#cl = rpc.Client()
#cl.run()

#base_list = rpc.DBList({'foo'})
#result_list = cl.append('bar', base_list)

#print("Result: {}".format(result_list.value))

#cl.stop()
