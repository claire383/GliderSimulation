#!/usr/bin/env python
# coding: utf-8

# In[92]:


#!/usr/bin/python3

#################################################################################################################

## creates a class that stores applicable ocean file (netcdf) data
## this class is a base class for other derived ocean model classes (i.e. Climatology, Hycom, etc.) 
## this class defines a three dimensional gridded interpolation method to get an ocean model parameter that is gridded by time, depth, lat & lon

#################################################################################################################
## imports

## standard imports
from scipy.interpolate import RegularGridInterpolator

#################################################################################################################
## define base class
## this class stores ocean file (netcdf) data
## this class defines an interpolation function

class oceanModel:

    #############################################################################################################
    ## define constructor
    ## this constructor stores ocean current files data (netcdf)
    
    def __init__(self):
        self.timeGrid = [0,0] # netcdf time grid, unix
        self.depthGrid = [] # netcdf depth grid, m
        self.latGrid = [] # netcdf lat grid, deg N
        self.lonGrid = [] # netcdf lon grid, deg E
        self.varGrid = [] # desired ocean variable grid
        self.interp = [0, 0, 0, 0]
        
    #################################################################################################################
    ## define function
    ## this function defines an interpolation method to get ocean currents at specified time, depth, lat & lon          
    
    def interp3(self,time_,depth,lat,lon,index): #takes 0.002 seconds to run
        
        if depth < 0:
            depth = 0

        ## call interpolator object function to interpolate for specified time, depth, lat & lon point
        lonUse = lon
        if(lon < 0):
            lonUse = 360+lon
        
        try:        
            var = self.interp[index]([time_,depth,lat,lonUse])
        except:
            print(time_)
            print(depth)
            print(lat)
            print(lonUse)
            raise Exception("Out of range")

        return var


# In[101]:


#!/usr/bin/python3

#########################################################

# this class reads & parses hycom type netcdf files
# files contain a single time per file; time is specified by 0-time given in file & elasped time in file filename
# this class updates the data stored in the base class oceanModel

# this class is a derived oceanModel class

#########################################################
# imports

# standard imports
import os
import sys
from datetime import datetime, timezone
from netCDF4 import Dataset

# add all directories to packages path
sys.path.insert(1,'../..')

# class import
#from oceanModel import *

#########################################################
# define class
# this class defines a derived class with inheritance
# class derived from oceanModel

# define child class
class hycomModel(oceanModel):
    
    #######################################################
    # define constructor
    # this constructor inherits all characteristics (self & functions) from oceanModel class
    # this constructor stores ocean file (netcdf) data
    
    pass
		
    #######################################################
    # define function
    # this function returns the timespan covered by the stored ocean data
    # define method to detect and save applicable data to class & to call 'interp' function to get 
    # interpolated water velocities
	
    def timeWindow(self):
        
        return self.timeGrid[0],self.timeGrid[-1]
	
    #######################################################
    # define function
    # this function reads & updates/saves applicable netcdf data to class (if necessary)
    
    def updateModel(self,path,t,dt): #updating model takes 3.7 seconds
        date1 = (datetime.utcfromtimestamp(int(t))).strftime('%Y%m%d')
        add = (dt/(24*60*60))+1
        date2 = int((datetime.utcfromtimestamp(int(t+dt))).strftime('%Y%m%d'))+int(add)
        
	# get directory list (NetCDF files list)	
        dir = os.listdir(path)
		
	# build array to store netcdf file times
        fileTimes = []

        for file in dir:
            if file.endswith('.nc'):
		# if desired date found in filename
                if (date1 in file) or (str(date2) in file):
                
                    # full path to individual netcdf file
                    file = '%s/%s'%(path,file)
                
                    # file base time
                    date0 = file.split('_')[-2] # filename string
                  
                    year0 = int(date0[:4])
                    month0 = int(date0[4:6])
                    day0 = int(date0[6:8])
                    
                    baseDate = datetime(year0,month0,day0) # datetime
                    baseTimestamp = baseDate.replace(tzinfo=timezone.utc).timestamp() # timestamp with timezone adjustment
                    
                    # time into model prediction
                    tau = file.split('_t')[-1] 
                    tau = tau.split('.')[0] # hours

                    # netcdf file time
                    timestamp = baseTimestamp + int(tau)*60*60 # unix timestamp
                    
                    timestamps = []
                    for line in fileTimes:
                        timestamps.append(line[0])
                    fileOptions = []
                    if timestamp in timestamps:
                        fileOptions.append([baseTimestamp,file])
                        idx = [i for i, x in enumerate(timestamps) if x == timestamp]
                        file1 = fileTimes[idx[0]][1]
                        date1 = file1.split('_')[-2] # filename string
                        year1 = int(date1[:4])
                        month1 = int(date1[4:6])
                        day1 = int(date1[6:8])
                        baseDate1 = datetime(year1,month1,day1) # datetime
                        baseTimestamp1 = baseDate1.replace(tzinfo=timezone.utc).timestamp() # timestamp with timezone adjustment
                        fileOptions.append([baseTimestamp1,file1])
                        fileOptions = sorted(fileOptions)
                        fileRm = fileOptions[0][1]
                        fileTimes.append([int(timestamp),file])
                        fileTimes = [x for x in fileTimes if fileRm not in x]
                            
                    else:
                        # append file time to all file times array
                        fileTimes.append([int(timestamp),file])

        # add desired bracketing file times to netcdf file times data
        fileTimes.append([int(t),'flag1'])
        fileTimes.append([int(t+dt),'flag2'])

        # sort file times array by time
        fileTimes = sorted(fileTimes)

        # find indices of files containing times bracketing interpolation times
        for i, item in enumerate(fileTimes):

            if 'flag1' in fileTimes[i][1]:
                ele1 = i
                                        
            if 'flag2' in fileTimes[i][1]:
                ele2 = i
        
        # save time bracketing files filenames       
        bracketFiles = []

        for j in range(ele1-1,ele2+2):
            if ('flag1' not in fileTimes[:][j]) & ('flag2' not in fileTimes[:][j]):
                bracketFiles.append(fileTimes[:][j])
            
        sorted(bracketFiles)
        
        if len(bracketFiles) != 2:
            tempBracket = []
            for i, item in enumerate(bracketFiles):
                if (i == 0) or (i == len(bracketFiles)-1):
                    tempBracket.append(bracketFiles[i])
                    
            bracketFiles = tempBracket
                    
        
  	# update bracketing times in class
        self.timeGrid = []
        for line in bracketFiles:

            self.timeGrid.append(line[0])
                        
	# get data from bracketing files & update in class
        dataset = Dataset(bracketFiles[0][1],'r')
            
        self.depthGrid = dataset.variables['depth'][:]
        self.latGrid = dataset.variables['lat'][:]
        self.lonGrid = dataset.variables['lon'][:]
              
        self.uGrid = [] 
        self.vGrid = []
        self.salGrid = [] 
        self.tempGrid = []
        for line in bracketFiles:

            dataset = Dataset(line[1],'r')
  
            u = dataset.variables['water_u']
            v = dataset.variables['water_v']
            S = dataset.variables['salinity']
            T = dataset.variables['water_temp']
            
            for ele in u:
                self.uGrid.append(ele)
                                            
            for ele in v:
                self.vGrid.append(ele)
                
            for ele in S:
                self.salGrid.append(ele)
                                                        
            for ele in T:
                self.tempGrid.append(ele)

        if self.timeGrid[-1] < self.timeGrid[0]:
            self.timeGrid = self.timeGrid[::-1]
            self.varGrid = self.varGrid[::-1]
    

        grid = [self.uGrid, self.vGrid, self.salGrid, self.tempGrid]
        
        for i in range(0, 4):
            self.interp[i] = RegularGridInterpolator((self.timeGrid,self.depthGrid,self.latGrid,self.lonGrid),grid[i],method='linear',bounds_error=True)

        


# In[102]:


#!/usr/bin/python3


#########################################################
# imports

# standard imports
import sys
from seawater import eos80 #make sure this is downloaded

# add all directories to packages path
sys.path.insert(1,'..')

# class imports
#from hycomModel import *

#########################################################
# define class

class oceanData:
    
    #######################################################
    # constructor
    # this constructor stores current position 
    
    def __init__(self,path):
        self.path = path # path to netcdf files
        self.model = hycomModel() # current model object

    #########################################################
    # define function
    # this function defines an integration method to establish next position (time, depth, lat & lon)
    # this function uses interpolation function from oceanModel class
       
    def rho(self,time_,depth,lat,lon):
        # if time step not within timespan of stored netcdf data, update model data
        # update model data by calling updateModel in specified currentModel class (climatology or hycom)
        timeframe = self.model.timeWindow()
        if (time_ not in range(timeframe[0],timeframe[-1])):
            self.model.updateModel(self.path,time_,1)
       
        # get salinity data
        S = self.model.interp3(time_,depth,lat,lon,2)

        # get temperature data
        T = self.model.interp3(time_,depth,lat,lon,3)
        
        # water density at ballast point, EOS-80; input (s,t,p)
        rho = eos80.dens(S,T,depth)
        
        return float(rho)
    
    #######################################################
    def currents(self, time_, depth, lat, lon): #takes 3.7 seconds, but likely bc it calls updateModel
        # if current files don't cover required timespan, update model data with new file
        
        timeframe = self.model.timeWindow()
        if (time_ not in range(timeframe[0],timeframe[-1])):
            print(datetime.fromtimestamp(time_))
            self.model.updateModel(self.path,time_,1)
        
        # get data on U currents (east-west)
        U = self.model.interp3(time_,depth,lat,lon,0)
        
        # get data on V currents (north-south)
        V = self.model.interp3(time_,depth,lat,lon,1) #try to interpolate not nan
        return U, V #U and V in m/s
    
    #######################################################
    def salAndTemp(self, time_, depth, lat, lon):
        
        # if current files don't cover required timespan, update model data with new file
        timeframe = self.model.timeWindow()
        if (time_ not in range(timeframe[0],timeframe[-1])):
            print(datetime.fromtimestamp(time_))
            self.model.updateModel(self.path,time_,1)
        
        # get data on salinity
        S = self.model.interp3(time_,depth,lat,lon,2)
        
        # get data on temp
        T = self.model.interp3(time_,depth,lat,lon,3) 
        return S, T


# In[87]:


#Example of how to use this code (with Pacific Ocean files):
#start_time = datetime.now()
#time = datetime(2015, 2, 2, 12, 0, 0)
#date = time.replace(tzinfo=timezone.utc).timestamp()
#oceanInfo = oceanData('C:/Users/lu386/Desktop1/APL Internship/20150202')

#print(oceanInfo.rho(date, 120, 45, -134))
    
#print(oceanInfo.currents(date, 4020, 20, -135))
#density = []

#for t in range(0, 12, 3):
    
    #for depth in range(0, 2000, 10):
        #density.append(oceanInfo.rho(date, depth, 50, -140))

#print("--- %s seconds ---" % (datetime.now() - start_time))


# In[ ]:

'''from datetime import timedelta
import numpy as np

startTime = datetime.now()
HYCOMFileDirectory = 'California HYCOM Files'
oceanInfo = oceanData(HYCOMFileDirectory)

date = datetime(2023, 9, 2, 1, 0, 0) #
lat = [32.8]
lon = -117.9


for j in lat:
    easting = []
    northing = []
    magnitude = []
    #depths = [0, 2, 4, 6, 8, 10, 12, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 500] #20 values
    depths = np.arange(0, 500, 10)

    for i in depths:
        u, v = oceanInfo.currents(date.replace(tzinfo=timezone(timedelta(hours=-7))).timestamp(), i, j, lon)
        easting.append(u[0])
        northing.append(v[0])
        magnitude.append(np.sqrt(u[0]**2+v[0]**2))
        date += timedelta(seconds=60)
    print("--- %s seconds ---" % (datetime.now() - startTime))

    import matplotlib.pyplot as plt

#print("--- %s seconds ---" % (datetime.now() - startTime))

    #fig, ax = plt.subplots(1)
    #ax[0].scatter(easting, depths)
    #ax[0].plot(easting, depths)
    #ax[1].scatter(northing, depths)
    #ax[1].plot(northing, depths)
    #ax[0].invert_yaxis()
    #ax[1].invert_yaxis()
    #ax[0].set(xlabel='Total Currents (m/s)', ylabel='Depth (m) ')
    #ax[1].set(xlabel='North-South Currents (m/s)', ylabel='Depth (m) ')

    plt.plot(magnitude, depths)
    plt.scatter(magnitude, depths)
    plt.xlabel('Total Currents (m/s)')
    plt.ylabel('Depth (m)')
    plt.gca().invert_yaxis()
    plt.show()'''