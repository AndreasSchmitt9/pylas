import netCDF4 as nc
import time
import os
from datetime import datetime


"""
Creates a netCDF file with an event dimension
"""
class dataSaver:



    def __init__(self, filename):

        base, ext = os.path.splitext(filename)
        self.filename=f"{base}_{datetime.now():%Y%m%d_%H%M%S}{ext}"
        os.makedirs(os.path.dirname(self.filename) or ".", exist_ok=True)


        self.nc_index = 0

        self.dataset = nc.Dataset(self.filename, mode='w', format='NETCDF4')

        self.dataset.createDimension('event', None) # Makes it possible to add an event to the dataset with unlimited length

        self.dataset.createVariable('timestamp', 'f8', ('event',)) # one float64 variable for every event
        self.dataset.createVariable('channel', 'i4', ('event',)) 
        self.dataset.createVariable('size_um', 'f8', ('event',)) 
        self.dataset.createVariable('passing_time', 'f4', ('event',))

        self.dataset.variables['timestamp'].units = 'seconds since 1970-01-01 00:00:00 UTC'
        self.dataset.variables['size_um'].units = 'micrometers'
        self.dataset.variables['passing_time'].units = 'microseconds'

        print("Created dataset:", filename)
    """
    Processes raw data and writes them to .nc file. 
    Example data format: 
    #98200:
    96,0.308,22.14;
    112,0.406,23.22;
    97,0.314,28.62;
    71,0.222,21.06;\r'
    """
    def process_packet(self, raw_bytes):
        text = raw_bytes.decode(errors='replace').strip()
        #print(f"Received data: {raw_bytes}") 
        #finds header
        if not text.startswith('#') or ':' not in text:
            return None
        header, _, body = text.partition(':')
        try:
            counter = int(header.lstrip('#'))
        except ValueError:
            return None

        events = []
        for chunk in body.rstrip(';').split(';'):
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split(',')
            if len(parts) != 3:
                continue
            try:
                events.append((int(parts[0]), float(parts[1]), float(parts[2]))) # allowed data format
            except ValueError:
                continue
            #write Data
            for channel, size_um, passing_time in events:
                i=self.nc_index
                self.dataset.variables['timestamp'][i] = time.time() # now!
                self.dataset.variables['channel'][i] = channel
                self.dataset.variables['size_um'][i] = size_um
                self.dataset.variables['passing_time'][i] = passing_time
                self.nc_index += 1
                #update dataset on disk
                if self.nc_index == 100: # saves every 1000 events 
                    print(f"Logging successfull")
                #print(self.nc_index)
            self.dataset.sync()
            #if self.nc_index == 100: # saves every 1000 events 
            #    print(f"Logging successfull")
        return events


    def stop(self):
        self.dataset.sync() # Ensure data is written to disk
        self.dataset.close()
    
