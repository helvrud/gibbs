import server_client_class
import time

clientB = server_client_class.Client(IP = '127.0.0.1', PORT = 10029)
time.sleep(1)
clientB.connect()
clientB.loop()