# In[2]:


#!/usr/bin/python3

"""
Script to automate downloading of HYCOM data in NetCDF form

Data from here:
http://ncss.hycom.org/thredds/ncss/grid/GLBv0.08/expt_53.X/data/2015/dataset.html
Update: data from here 
https://ncss.hycom.org/thredds/ncss/grid/GLBy0.08/expt_93.0/dataset.html



Sample URL built to get data:
URL = 'http://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_53.X/data/2015?'\
      'var=water_u_bottom&var=water_v_bottom&var=water_u&var=water_v'\
      '&north=22&west=-159&east=-157&south=20'\
      '&disableProjSubset=on'\
      '&horizStride=1'\
      '&time=2015-02-02T12%3A00%3A00Z'\
      '&vertCoord=&accept=netcdf4'
      
"""
#https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0?var=surf_el&var=salinity&var=water_temp&var=water_u&var=water_v&north=31.0&west=-79.0&east=-76.0&south=28.0&disableProjSubset=on&horizStride=1&time_start=2023-6-20T12%3A00%3A00Z&time_end=2023-07-20T09%3A00%3A00Z&timeStride=1&vertCoord=&accept=netcdf4

# Standard imports
#import sys
import urllib.request
import datetime

# =========================================================================
# Application start
# =========================================================================

# Specify file limits
latMin=32.7 #south
latMax=33.4 #north
lonMin=-118.7 #west
lonMax=-117.2 #east

# Time limits
yearStart=2023; monthStart=6; dayStart=9; hourStart=0
yearEnd=2023;   monthEnd=6;  dayEnd=15;  hourEnd=12
# Delta (in hours)
dHour = 3

# Convert end and deltas to datetime objects
endTime =  datetime.datetime(yearEnd,monthEnd,dayEnd,hourEnd)
dTime = datetime.timedelta(hours=dHour)

# Init
thisTime = datetime.datetime(yearStart,monthStart,dayStart,hourStart)

# Go until final time is reached
while( thisTime <= endTime ):

    # Extract date/time parts
    year = thisTime.year
    month = thisTime.month
    day = thisTime.day
    hour = thisTime.hour
    print(' - Time (YY,MM,DD,HH): %d,%d,%d,%d' % 
          (year,month,day,hour))

    # Build URL    
    URL = 'http://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0?'          'var=salinity&var=water_temp&var=water_u&var=water_v'          '&north=%f&west=%f&east=%f&south=%f'          '&disableProjSubset=on'          '&horizStride=1'          '&time=%04d-%02d-%02dT%02d' % (latMax,lonMin,lonMax,latMin,year,month,day,hour)
    URL = URL + '%3A00%3A00Z&vertCoord=&accept=netcdf4'

    # Create local filename
    localNetCDF = 'HYCOM_%04d%02d%02d_t0%02d.nc' % (year,month,day,hour)

    # Do the download
    print('   Downloading to file: %s ...' % localNetCDF)
    try:
      urllib.request.urlretrieve(url=URL,filename=localNetCDF)
    except urllib.error.HTTPError as e:
       print(e.reason)
    print('   Local file created')

    # Bump the time
    thisTime = thisTime + dTime


print('\n === DONE ===\n')


# In[ ]: