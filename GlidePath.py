#libary imports
import seawater as sw
import numpy as np
from datetime import datetime, timezone, timedelta
import csv
import simplekml
from scipy import interpolate
import matplotlib.pyplot as plt

#class imports
from OceanData import oceanData  #reads NETCDFs for currents
from NavUtils import bearing, projectPositionXY, distance  #contains mathematic functions including conversioin XY <-> lat/lon
import BathyReader  #interpolates depth from gebco
#CHECK THIS - CHANGED FOR HOVER??
from BuoyancyEngine import buoyancyEngine #operated mechanism that changes teh glider's buoyancy
from ConfigReader_v2 import configReader_v2  #reads config file
#MAKE ENERGY DIAGRAM
#from EnergyGrapher import grapher  #graphs energy used over time
from PhiSpeeds import speedCalc
from glidePathGraph import plotter


class glider:
    
    def __init__(self, startPoint, endPoint, startDate):
                
        self.speed = 0
        maxPitchDegrees = configRead.getInt('Glider', 'maxPitchAngle') 
        self.maxPitchRadians = maxPitchDegrees * np.pi / 180 #converts to radians

        self.startPoint = startPoint
        self.lat, self.lon = startPoint
        self.endPoint = endPoint
        self.bearing = bearing(startPoint[0], startPoint[1], endPoint[0], endPoint[1]) #great circle bearing in degrees from North
        self.proximityToTarget = configRead.getInt('General', 'proximityToTarget')

        HYCOMFileDirectory = configRead.getString('General', 'HYCOMFileDirectory') #folder that has netcdf files
        self.oceanInfo = oceanData(HYCOMFileDirectory)
        
        self.bathyreader = BathyReader.bathymetryReader(configRead.getString('General', 'gebcoFile')) #download from link above

        self.depth = 0 #meters from ocean surface
        self.maxDepth = configRead.getInt('Glider', 'maxDepth')

        self.date = startDate
        self.timeStart = startDate
        self.timeStartIteration = startDate
        self.interval = configRead.getInt('General', 'interval') #size of timestep used in this simulation (in this case, 60 seconds)
        self.loiterTime = configRead.getInt('General', 'loiterTime') #number of minutes glider spends at surface without trying to move
        self.UTCOffset = configRead.getInt('Location/Time', 'UTCOffset')
        
        startingOil = configRead.getInt('Glider', 'startingOil')
        totDisplacement = configRead.getInt('General', 'totDisplacement')
        buoyancyMin = configRead.getInt('Glider', 'buoyancyMin')
        buoyancyMax = configRead.getInt('Glider', 'buoyancyMax')
        pumpingPeriod = configRead.getInt('General', 'pumpingPeriod')
        totBatteryPower = configRead.getFloat('General', 'totBatteryPower')
        self.startingEnergy = totBatteryPower
        pumpRate = configRead.getInt('General', 'pumpRate')
        
        self.rhoR = configRead.getInt('General', 'neutralDens')
        self.gliderVolume = configRead.getInt('General', 'gliderVolume')
        self.neutralState = self.rhoR * (self.gliderVolume/(10^6))
        
        self.buoyancyengine = buoyancyEngine(startingOil, totDisplacement, buoyancyMin, buoyancyMax, pumpingPeriod, totBatteryPower, pumpRate)
        
        self.hotelLoad = configRead.getInt('General', 'hotelLoad') #in Watts
        self.hotelLoadUsed = 0
        
        clA = configRead.getFloat('Glider', 'clA')
        clB =  configRead.getFloat('Glider', 'clB')
        cdA = configRead.getFloat('Glider', 'cdA')
        cdB = configRead.getFloat('Glider', 'cdB')
        phis, vxs, vzs = speedCalc(clA, clB, cdA, cdB)
    
        self.xVelPartInterp = interpolate.interp1d(phis, vxs)
        self.zVelPartInterp = interpolate.interp1d(phis, vzs)
        self.phiCurr = 0
        
        self.salPrev = [0]
        self.tempPrev = [0]
        self.northPrev = [0]
        self.eastPrev = [0]
        
        #initializing values and arrays
        self.times = [0] #in minutes
        self.lats = [self.lat] #where the glider actually is underwater
        self.lons = [self.lon]
        self.depths = [0] #distance (meters) from ocean surface
        self.energies = [self.buoyancyengine.batteryPower]
        self.buoyancyStates = [self.buoyancyengine.oilInBalloon]
        self.pitchAngles = [self.phiCurr]
        self.betweenSurfaceTimes = []

        self.surfaceNum = 0 #number of times glider surfaces - equal to number of dives
        self.reachSurfaceLat = [self.lat] #where the glider is when it surfaces
        self.reachSurfaceLon = [self.lon]
        self.leaveSurfaceLat = [self.lat] #where the glider is after loitering on the surface (subject to ocean currents)
        self.leaveSurfaceLon = [self.lon]
        description = 'Remaining energy: %.2f kWh \n Position (degrees lat, degrees lon): (%.2f, %.2f) \n Time: %.2f minutes' % (self.buoyancyengine.batteryPower, self.lat, self.lon, 0)
        self.surfaceDescriptions = [description]
        
        self.destDist = 0
        self.tripTime = 0
        
        self.speeds = []
        self.bearings = [] #great circle bearing

        self.totalDistX = 0 #total distance (meters) traveled
        self.totalDistY = 0

        self.lat_nocurrents = self.lat #tracks where the glider would surface if there were no currents
        self.lon_nocurrents = self.lon
        self.noCurrLats = []
        self.noCurrLons = []
        self.dac_north = [] #depth_averaged northing currents
        self.dac_east = []

        self.diving = True #toggles glider's diving or ascending maneuver
        self.loitering = False
        self.starting = True
        self.onFloor = False
        
        self.done = False
        
    def update(self, endTime):
        
        timeStep = self.interval
        
        #out of range of NetCDFs --> end program
        if self.date > endTime: #end sim if overtime - outside of NetCDF range
            timeStep = 0
            print('Out of range')
            self.done = True
            
        
        #loitering (beginning, end, or in between cycles)
        elif self.loitering: #loiters at beginning, end, and whenever it surfaces
            
            for n in range(self.loiterTime):
            
                #find currents from HYCOM
                easting1, northing1 = self.oceanInfo.currents(self.date.replace(tzinfo=timezone(timedelta(hours=self.UTCOffset))).timestamp(), self.depth, self.lat, self.lon) #meters/second
                
                #CHECK CURRENTS
                if abs(easting1[0]) > 10 or abs(northing1[0]) > 10:
                    easting1 = self.eastPrev
                    northing1 = self.northPrev
                else:
                    self.eastingPrev = easting1
                    self.northingPrev = northing1
                
                #update position
                self.lat, self.lon = projectPositionXY(self.lat, self.lon, northing1[0] * 60, easting1[0] * 60)
                
                #calculate total distance traveled (m)
                self.totalDistX += abs(easting1[0]) * 60
                self.totalDistY += abs(northing1[0]) * 60
                
                self.lat_nocurrents = self.lat
                self.lon_nocurrents = self.lon

                #update glider heading when it surfaces
                self.bearing = bearing(self.lat, self.lon, self.endPoint[0], self.endPoint[1])
            
            self.loitering = False
            self.starting = True
            timeStep = self.loiterTime * 60 #converts to seconds - time updates at bottom of main
            
            self.diving = True
                
            self.leaveSurfaceLat.append(self.lat)
            self.leaveSurfaceLon.append(self.lon)
                
            #check if glider is near target destination --> end sim
            if (distance(self.lat, self.lon, self.endPoint[0], self.endPoint[1]) < self.proximityToTarget):
                print('Reached destination!')
                    
                self.done = True
                    
                #self.destDist = distance(self.startPoint[0], self.startPoint[1], self.lat, self.lon)
                #self.tripTime = ((self.date + timedelta(seconds=timeStep)).timestamp() - self.timeStart.timestamp())/60 #in minutes
                
        
        
        #normal function 
        else:
            
            if self.depth > 0:
                self.starting = False
            
            if (self.diving):
                turned = self.buoyancyengine.deflateBalloon(self.depth) #descend maneuver
                
            else:
                turned = self.buoyancyengine.inflateBalloon(self.depth) #ascend maneuver
                
            if (turned):
                timeStep = self.buoyancyengine.pumpingPeriod
            
            salinity, temp = self.oceanInfo.salAndTemp(self.date.replace(tzinfo=timezone(timedelta(hours=self.UTCOffset))).timestamp(), self.depth, self.lat, self.lon)
            
            if(abs(salinity[0]) > 35 or abs(salinity[0]) < 33 or abs(temp[0]) > 20 or abs(temp[0]) < 3):
                salinity = self.salPrev
                temp = self.tempPrev
            else:
                self.salPrev = salinity
                self.tempPrev = temp
            
            densCurr = sw.dens(salinity[0], temp[0], self.depth*1.45038*0.689476)
            33.2, 34.5
            if abs(densCurr - 1015) <= 1:
                print(temp[0])
            
            vertical_velocity = self.velocity(timeStep, densCurr)
            
            
            #check if glider has hit depth limit --> should start ascending
            if (self.depth >= self.maxDepth):
                self.diving = False
                
                
            #check if glider has surfaced and is not on its way down
            elif (self.depth <= 0 and not self.loitering and not self.starting):
                #update number of times glider surfaces (to be printed to console after simulation ends)
                self.surfaceNum += 1

                #interpolate back in time to when the glider actually reached the surface (could be above the surface - could interpolate back to lat and lon too?)
                time1 = np.interp(0, [self.depth - vertical_velocity*timeStep, self.depth], [self.date.timestamp(), (self.date + timedelta(seconds=timeStep)).timestamp()])
                self.date = datetime.fromtimestamp(time1)
                self.depth = 0
                #self.speed = 0
                    
                timeStep = time1 - self.date.timestamp()

                #update location for kml file
                self.reachSurfaceLat.append(self.lat)
                self.reachSurfaceLon.append(self.lon)
                    
                currTime = ((self.date + timedelta(seconds = timeStep)).timestamp() - self.timeStart.timestamp())/60 #in minutes
                description1 = 'Remaining energy: %.2f kWh \n Position (degrees lat, degrees lon): (%.2f, %.2f) \n Time: %.2f minutes' % (self.buoyancyengine.batteryPower, self.lat, self.lon, currTime)
                self.surfaceDescriptions.append(description1)

                #calculate depth-averaged current (difference between real lat/lon and lat/lon without currents since last surfacing)
                difference = distance(self.lat, self.lon, self.lat_nocurrents, self.lon_nocurrents)
                angle = bearing(self.lat_nocurrents, self.lon_nocurrents, self.lat, self.lon) * np.pi / 180 #units in radians
                diveTime = int((self.date - self.timeStartIteration).total_seconds())
                self.dac_north.append(difference * np.cos(angle) / diveTime)
                self.dac_east.append(difference * np.sin(angle) / diveTime)
                
                self.betweenSurfaceTimes.append(diveTime/60)
                
                #check if glider is near target destination --> end sim
                if (distance(self.lat, self.lon, self.endPoint[0], self.endPoint[1]) < self.proximityToTarget):
                    print('Reached destination!')

                    self.done = True
                    
                    #self.destDist = distance(self.lat, self.lon, self.endPoint[0], self.endPoint[1])
                    #self.tripTime = ((self.date + timedelta(seconds=timeStep)).timestamp() - self.timeStart.timestamp())/60 #in minutes
                                        
                #Next iteration, loiter at surface
                self.loitering = True
                
                self.timeStartIteration = self.date #reset for next iteration
                
            #check if glider hits ocean floor --> bounce off
            oceanFloor = self.bathyreader.getDepth(self.lat, self.lon)
            if (oceanFloor[0] - self.depth <= 0):
                
                if not self.onFloor:
                    print('Bounced off ocean floor')
                    self.depth = oceanFloor[0]
                    self.onFloor = True
                    
                    '''#linear interpolation of time from depth
                    #moment where the vehicle actually hit depth limit
                    time1 = np.interp(oceanFloor[0], [self.depth - vertical_velocity * timeStep, self.depth], [self.date.timestamp(), (self.date + timedelta(seconds=timeStep)).timestamp()])
                    
                    #update current time and depth
                    timeStep = time1 - self.date.timestamp() #should give it in seconds??'''
                
                self.diving = False
                
        
        #hotel load runs always
        self.buoyancyengine.batteryPower -= (self.hotelLoad*(timeStep/60/60))/1000 #converts from Watts to kWh
        self.hotelLoadUsed += (self.hotelLoad*(timeStep/60/60))/1000
        
        #update time
        self.date += timedelta(seconds=timeStep)
        
        #updating important quantities
        self.times.append((((self.date).timestamp() - self.timeStart.timestamp())/60)) #in minutes
        self.lons.append(self.lon)
        self.lats.append(self.lat) 
        self.depths.append(self.depth)
        self.energies.append(self.buoyancyengine.batteryPower)      
        self.speeds.append(self.speed)
        self.bearings.append(self.bearing)
        self.buoyancyStates.append(self.buoyancyengine.oilInBalloon)
        self.pitchAngles.append(self.phiCurr)
        self.noCurrLats.append(self.lat_nocurrents)
        self.noCurrLons.append(self.lon_nocurrents)
        
        
    def velocity(self, timeStep, densCurr):
            
        halfDens = self.buoyancyengine.totDisplacement/2
                
        dV = self.buoyancyengine.oilInBalloon - halfDens
        #negative if moving toward surface (negative depth)
        Fbuo = 9.8 * (self.rhoR*self.gliderVolume*(10**-6) - densCurr*(self.gliderVolume+dV)*(10**-6))
        Fmax = 9.8 * (self.rhoR*self.gliderVolume*(10**-6) - densCurr*(self.gliderVolume+(self.buoyancyengine.minOil-halfDens))*(10**-6))
        
        self.phiCurr = (self.maxPitchRadians/Fmax)*Fbuo
                
        factor = 1
        if (Fbuo < 0): #diving is positive depth direction
            factor = -1
                
        #separate total glider velocity into vertical speed (up/down) and lateral speed (x and y axes)
        multiplier = np.sqrt(2*abs(Fbuo/densCurr))
        vertical_velocity = factor * multiplier * self.zVelPartInterp(abs(self.phiCurr)) #m/s
        lateral_velocity = multiplier * self.xVelPartInterp(abs(self.phiCurr))
        
        #if on surface, should not go up more
        if self.depth <= 0 and Fbuo < 0:
            self.depth = 0
            
            lateral_velocity = 0
            vertical_velocity = 0
            self.phiCurr = 0
            
            
        #if on sea floor, shouldn't move until buoyancy state switches sign
        if self.onFloor and self.buoyancyengine.oilInBalloon <= self.buoyancyengine.maxOil*0.8:
            lateral_velocity = 0
            vertical_velocity = 0
        elif self.onFloor and self.depth < self.maxDepth:
            self.onFloor = False
                    
        self.speed = np.sqrt(vertical_velocity**2 + lateral_velocity**2)
                
        '''if vertical_velocity < 0: #ascending
            self.diving = False
        else:
            self.diving = True'''
                    
                
        #split lateral velocity into northing and easting (thru-water speed) and add ocean currents
        easting, northing = self.oceanInfo.currents(self.date.replace(tzinfo=timezone(timedelta(hours=self.UTCOffset))).timestamp(), self.depth, self.lat, self.lon) #meters/second
        
        #CHECK CURRENTS
        if abs(easting[0]) > 10 or abs(northing[0]) > 10:
            easting = self.eastPrev
            northing = self.northPrev
        else:
            self.eastingPrev = easting
            self.northingPrev = northing
                
        eastingV = lateral_velocity * np.sin(self.bearing * np.pi / 180)
        northingV = lateral_velocity * np.cos(self.bearing * np.pi / 180)

        #update location & depth
        self.depth += vertical_velocity * timeStep
        self.lat, self.lon = projectPositionXY(self.lat, self.lon, (northingV + northing[0]) * timeStep, (eastingV + easting[0]) * timeStep) 

        #calculate total distance traveled (m)
        self.totalDistX += abs(eastingV + easting[0]) * timeStep
        self.totalDistY += abs(northingV + northing[0]) * timeStep
        
        self.destDist += np.sqrt((abs(eastingV + easting[0]) * timeStep)**2 + (abs(northingV + northing[0]) * timeStep)**2)
        self.tripTime += (timeStep)/60

        #calculate hypothetical location of glider if ocean currents didn't exist
        self.lat_nocurrents, self.lon_nocurrents = projectPositionXY(self.lat_nocurrents, self.lon_nocurrents, northingV * timeStep, eastingV * timeStep)
        
        return vertical_velocity
        
        

######################################################
#START OF PROGRAM
######################################################
print('running gliders...')

configRead = configReader_v2()
configRead.loadFile('SoCalData+Sim/gliderConfig.dat')

#setting start and end times of simulation
startYear = configRead.getInt('Location/Time', 'startYear')
startMonth = configRead.getInt('Location/Time', 'startMonth')
startDay = configRead.getInt('Location/Time', 'startDate')
startHour = configRead.getInt('Location/Time', 'startHour')

startTime = datetime(startYear, startMonth, startDay, startHour, 0, 0)

endYear = configRead.getInt('Location/Time', 'endYear')
endMonth = configRead.getInt('Location/Time', 'endMonth')
endDay = configRead.getInt('Location/Time', 'endDay')
endHour = configRead.getInt('Location/Time', 'endHour')

endTime = datetime(endYear, endMonth, endDay, endHour, 0, 0)

#setting up lat/lon box of travel
minLat = configRead.getFloat('Location/Time', 'minLat')
maxLat = configRead.getFloat('Location/Time', 'maxLat')
minLon = configRead.getFloat('Location/Time', 'minLon')
maxLon = configRead.getFloat('Location/Time', 'maxLon')

#setting start positions of glider 1
startLat = configRead.getFloat('Location/Time', 'startLat')
startLon = configRead.getFloat('Location/Time', 'startLon')
endLat = configRead.getFloat('Location/Time', 'endLat')
endLon = configRead.getFloat('Location/Time', 'endLon')

#creating glider object
glider1 = glider([startLat, startLon], [endLat, endLon], startTime)


#running glider object in parallel
done = False
while(not done):
    glider1.update(endTime)
    
    if (glider1.done):
        plt.plot(glider1.lons, glider1.lats)
        plt.plot([-118.7, -118.7], [32.7, 33.4], linestyle='dashed')
        plt.plot([-117.2, -117.2], [32.7, 33.4], linestyle='dashed')
        plt.plot([-118.7, -117.2], [32.7, 32.7], linestyle='dashed')
        plt.plot([-118.7, -117.2], [33.4, 33.4], linestyle='dashed')
        plt.plot(-117.51995981980528, 33.166979172139825, 'gx')
        plt.plot(-118.48001, 32.97972, 'rx')
        plt.grid()
        plt.show()
    
    done = glider1.done



rowsToWrite = []

for l in range(len(glider1.dac_east)):
    row = [glider1.reachSurfaceLat[l], glider1.reachSurfaceLon[l], glider1.dac_east[l], glider1.dac_north[l]]
    rowsToWrite.append(row)
    

#csv of current quantities
fileName = 'SoCalSimDAC_' + str(glider1.maxDepth) + '.csv'

with open(fileName, 'w') as file:
    csvwriter = csv.writer(file)
    
    header = ['lat', 'lon', 'dac_east', 'dac_north']
    csvwriter.writerow(header)
    
    csvwriter.writerows(rowsToWrite)


'''#plotting what would happen without currents
plt.plot(glider1.noCurrLons, glider1.noCurrLats)
plt.plot([-118.7, -118.7], [32.7, 33.4], linestyle='dashed')
plt.plot([-117.2, -117.2], [32.7, 33.4], linestyle='dashed')
plt.plot([-118.7, -117.2], [32.7, 32.7], linestyle='dashed')
plt.plot([-118.7, -117.2], [33.4, 33.4], linestyle='dashed')
plt.plot(-117.51995981980528, 33.166979172139825, 'gx')
plt.plot(-118.48001, 32.97972, 'rx')
plt.grid()
plt.show()'''

'''#plotting important quantities
plotName = configRead.getString('General', 'desiredFileTitle') + '.png'
plotter(glider1.times, glider1.depths, glider1.energies, glider1.buoyancyStates, glider1.pitchAngles, plotName)


#Writing data to csv file
print('creating csv file...')


rowsToWrite = []
for h in range(len(glider1.times)):
    currentRow = [glider1.times[h]]
    
    
    currentRow.append(round(float(glider1.lats[h]), 5)) #lat
    currentRow.append(round(float(glider1.lons[h]), 5)) #lon
    currentRow.append(round(float(glider1.depths[h]), 1)) #depth
    currentRow.append(round(float(glider1.energies[h]), 3)) #energy
    #currentRow.append(round(float(glider1.dac_north[h]), 5)) #north depth averaged currents
    #currentRow.append(round(float(glider1.dac_east[h]), 5)) #east depth averaged currents
        
    rowsToWrite.append(currentRow)

titleCSV = configRead.getString('General', 'desiredFileTitle') + '.csv'

file = open(titleCSV, 'w')
writer = csv.writer(file)

header = ['time (s)', 'lat (deg)', 'lon (deg)', 'depth (m)', 'energies (kWh)']

writer.writerow(header)
writer.writerows(rowsToWrite)

file.close()


#making kml file to display surfacing points
print("creating kml file...")

kml = simplekml.Kml()

#creating points in kml file
for z in range(len(glider1.reachSurfaceLat)):
    
    pnt1 = kml.newpoint(coords = [(glider1.reachSurfaceLon[z], glider1.reachSurfaceLat[z])])
            
    pnt1.description = glider1.surfaceDescriptions[z]


titleKML = configRead.getString('General', 'desiredFileTitle') + '.kml'
kml.save(titleKML)'''

    
#printing important values
print()
print('#################################')

str1 = '  Time of trip to destination: %.2f minutes' % (glider1.tripTime) 
print(str1)
str2 = '  Distance of trip to destination: %.2f meters' % (glider1.destDist)
print(str2)
str3 = '  Times surfaced: %i' % (glider1.surfaceNum)
print(str3)
hotUse = glider1.hotelLoadUsed
propUse = glider1.buoyancyengine.propulsionPowerUsed
str4 = '  Energy used: %.2f kWh from hotel load + %.2f kWh from propulsion = %.2f kWh total' % (hotUse, propUse, hotUse + propUse)
print(str4)
str5 = '  Average time of each dive: %.2f minutes' % (np.average(glider1.betweenSurfaceTimes))
print(str5)
str6 = '  Distance to endpoint: %.2f meters' % (distance(glider1.lat, glider1.lon, glider1.endPoint[0], glider1.endPoint[1]))
print(str6)
    
print('#################################')
print()

print("\n------DONE------\n")