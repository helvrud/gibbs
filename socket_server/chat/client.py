import server_client_class

ID = input("ID?")

client = server_client_class.Client(IP = '127.0.0.1', PORT = 10003, ID = ID)

client.connect()

client.say_hello()

client.loop()
