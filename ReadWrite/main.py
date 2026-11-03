#from connect import init, read_live_data, stop
import socket
import signal
import time
import json
import sys
from ReadWrite.createnc import dataSaver
from ReadWrite.connect import LiveSocket
from multiprocessing import Process, Queue, Event, Manager
from settings import cfg

def run_read_write(control_list_shared=None):

    rw = cfg["ReadWrite"]                                   
    ip = rw["WELAS_LISTEN_IP"]
    port = rw["WELAS_LISTEN_PORT"]
    dataset= rw["dataset"]

    print("Initializing Read and Write...")
    live_socket = LiveSocket(ip, port, "udp")
    nc_ds=dataSaver(dataset, control_list=control_list_shared)

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
