import socket
import signal


class LiveSocket:
    #Automatically initializes a socket connection when creating an object
    def __init__(self, host, port, mode): 
        if mode == "udp":
            print("Initializing UDP socket...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # AF_INET -> Tells Socket to use IPv4, SOCK_STREAM -> Tells Socket to use UDP
        elif mode == "tcp":
            print("Initializing TCP socket...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET -> Tells Socket to use IPv4, SOCK_STREAM -> Tells Socket to use TCP
        else:
            raise ValueError("Invalid mode. Use 'tcp' or 'udp'.")

        # Allows quick reloading and no stuck addresses
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Actually initialize the socket
        self.sock.bind((host, port))

    def read_live_data(self):
        #print("hello world")
        #while True:
        data, adress = self.sock.recvfrom(65536) # buffer size is 65536 bytes
            #print(f"Received data from {adress}: {data}")
        return data 

    def stop(self):
        self.sock.close()
