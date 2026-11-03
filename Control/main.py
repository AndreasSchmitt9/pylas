
import queue
import time
import csv
from pathlib import Path
from datetime import datetime
from settings import cfg, reload_if_changed
from Control.postprocess import Postprocessor
from Control.preprocess import Preprocessor
from Control.pid import PID
    # Preprocess Input: data_queue, Output : Control_data
    # pid: INPUT Control_data, Output: Control_signal (Aerosol Injection System Setpoint (desiredConcentration))
    # Postprocess Input: Control_signal, Output: UDP_signal
    
def run_control(control_list_shared):



    #INIT
    print("Initializing Control...")
    pre = Preprocessor()
    pid = PID()
    load_params(pid,pre)
    post = Postprocessor()
    next_tick = time.monotonic()


    p=cfg["pid"]
    DT_S=p["DT_S"]
   
    try:
        #Run at 10Hz
        while True:
            if reload_if_changed():            # True only when the file changed
                load_params(pid, pre)
                print("Params: reloaded", flush=True)

            #Append all events in list and delete list in shared memory
            events=control_list_shared[:]
            del control_list_shared[:]
            
            if events: 

                for timestamp, channel, size_um, passing_time in events:
                    pre.push(timestamp, size_um)

                pid.update(pre.calculate_lwc()) # Set the newest lwc as input to the PID controller
                pid_output = pid.output() # Get the control signal from the PID controller
                post.publish(pid_output) # Send the control signal to the matlab script

            # Make sure the loop runs at a fixed interval
            next_tick += DT_S
            sleep_time = next_tick - time.monotonic()
            time.sleep(max(0, sleep_time))


    finally:
        post.close()  # Ensure the socket is closed when the loop exits

def load_params(pid, pre):
    """Copy the current values from settings.toml into pid."""
    pid_p=cfg["pid"]
    pid.kp = pid_p["KP"]
    pid.ki = pid_p["KI"]
    pid.kd = pid_p["KD"]
    pid.lwc_target = pid_p["LWC_TARGET"] 
    pid.gain = pid_p["GAIN"]
    pid.dt=pid_p["DT_S"]
    pid.min_conc = pid_p["MIN_CONCENTRATION"]
    pid.max_conc = pid_p["MAX_CONCENTRATION"]

    pid.lwc_omega = pid_p["OMEGA"] 
    pid.lwc_0 = pid_p["LWC_0"] 
    pid.amplitude = pid_p["AMPLITUDE"]

    #Reset control values:
    pid.integral = 0.0
    pid.last_error = None
    pid.last_output = 0.0


    pre_p=cfg["pre"]
    pre.WINDOW_S = pre_p["WINDOW_S"]
    pre.RHO_WATER_G_M3=pre_p["RHO_WATER_G_M3"]
    pre.VOLUME = pre_p["WIDTH"]*pre_p["DEPTH"]*pre_p["VELOCITY"]*pre.WINDOW_S*1e6 # um^3

    ##VOLUME = 3.077e13 #WIDTH* DEPTH * VELOCITY * WINDOW_S*1e6  um^3 # Roughly 0.02l


    