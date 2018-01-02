import threading
import MultiChatServer
import MultiChatClient

class ChatServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        MultiChatServer.main()

class ChatClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        MultiChatClient.main()

if __name__ == '__main__':
    chatclient = ChatClient()
    chatserver = ChatServer()
    chatserver.start()
    chatserver.join()
    chatclient.start()
