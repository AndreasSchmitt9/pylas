# root main.py
from multiprocessing import Process, Queue, Event, Manager
from ReadWrite.main import run_read_write
from Control.main import run_control  
from ui.plotter import run_plotter
from settings import cfg

if __name__ == "__main__":
    manager = Manager()
    control_list_shared = manager.list()  # Shared list for control data
    #plotted_queue= Queue(maxsize=1000)

    p1 = Process(target=run_read_write, args=(control_list_shared,))
    p2 = Process(target=run_control, args=(control_list_shared,))
    p3 = Process(target= run_plotter, args=(control_list_shared,))

    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()