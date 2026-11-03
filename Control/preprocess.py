# This code preprocesses data, extracts liquid-Water content
import math
from collections import deque

# (WxDxH) Measurement Volume
#welas ® 2070: approx. 66 µm x 68 µm x 68 µm* -> 305184
#welas ® 2100: approx. 81 µm x 77 µm x 77 µm* -> 480249
#welas ® 2200: approx. 172µm x 155 µm x 155 µm* -> 4132300
#welas ® 2300: approx. 144 µm x 227 µm x 227 µm* -> 7420176
#welas ® 2500: approx. 313 µm x 493 µm x 493 µm* -> 76074337

class Preprocessor:
    def __init__(self):
        self.events = deque()  
        self.WINDOW_S=10
        self.RHO_WATER_G_M3 = 1.0e6 
        self.VOLUME=0.125

    def _prune_old_events(self, current_timestamp):
        # Remove any events older than 10s relative to the latest data
        cutoff = current_timestamp - self.WINDOW_S
        #print(self.events[0][0] - cutoff)
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def push(self, timestamp, size_um):
        self.events.append((timestamp, size_um))
        self._prune_old_events(timestamp)
    
    def calculate_lwc(self):
        if not self.events:
            print("No live-data available for LWC calculation.")
            return 0.0

        sum_d3 = 0.0
        for t,dm in self.events:
            sum_d3 += (dm ) ** 3 # dm in micrometers, so dm^3 in micrometers^3

        #print(f"lwc: {(sum_d3 * RHO_WATER_G_M3 * math.pi) / (6 * VOLUME):.6f}  g/m^3") # g/m^3
        span = self.events[-1][0] - self.events[0][0]
        #print(f"n={len(self.events)} span={span:.2f}s window={self.WINDOW_S} volume={self.VOLUME:.3e}", flush=True)
        return (sum_d3 * self.RHO_WATER_G_M3 * math.pi) / (6 * self.VOLUME) # g/m^3
    