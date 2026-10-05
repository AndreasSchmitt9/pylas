#from connect import init, read_live_data, stop
import socket
import signal
from createnc import dataSaver
from connect import LiveSocket
import time
import sys

#Setup
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 56790
NUM_CHANNELS = 256
dataset = "data/findme.nc"


def main():

    print("Initializing...")
    live_socket = LiveSocket(LISTEN_IP, LISTEN_PORT, "udp")
    nc_ds=dataSaver(dataset)

    #Stops the process cleanly
    def stop(signum=None, frame=None):
        live_socket.stop()
        nc_ds.stop()
        print("Stopped cleanly.")
        sys.exit(0)
    # calls the stop function when ctrl+c is pressed
    signal.signal(signal.SIGINT, stop)

    try:
        while True: 
            data = live_socket.read_live_data() # read data
            events=nc_ds.process_packet(data) # write data
    except Exception as e:
        print(f"Error: {e}")
        stop(None,None)


if __name__ == "__main__":
    main()