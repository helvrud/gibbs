import server_client_class

clientA = server_client_class.Client(IP = '127.0.0.1', PORT = 10029)
clientA.connect()

msg = server_client_class.Message()
msg.data = 'echo test'
msg.receiver = clientA.addr
msg.sender = clientA.addr

clientA.send_object(msg)

echo = clientA.recv_object()

print("Message echo successful")
print(echo.data)

