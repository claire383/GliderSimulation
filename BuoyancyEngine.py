#library imports
from scipy import interpolate
import csv

class buoyancyEngine:
    def __init__(self, startingOil, totDisplacement, buoyancyMin, buoyancyMax, pumpingPeriod, totBatteryPower, pumpRate):
        self.totDisplacement = totDisplacement #in cc's
        self.minOil = buoyancyMin #in cc's
        self.maxOil = buoyancyMax #in cc's
        self.startOil = startingOil
        
        self.oilInBalloon = startingOil #cc's external
        self.pumpingPeriod = pumpingPeriod #in seconds
        
        self.pumpRate = pumpRate
        
        self.batteryPower = totBatteryPower #in kWh
        self.propulsionPowerUsed = 0
        
        pressures = []
        energies = []
        with open("glidersim_v3/flowRateData.csv", "r") as file:
            csvreader = csv.reader(file)
    
            csvreader.__next__() #gets past header
            
            for row in csvreader:
                pressures.append(float(row[0]))
                energies.append(float(row[2]))
        
        self.energyUsed = interpolate.interp1d(pressures, energies) #interpolates energy usage per pressure


    def inflateBalloon(self, depth): #ascend maneuver (up from depth limit) --- 0%->100%
        
        turned = False #true if oil was pumped
        if (self.oilInBalloon < self.maxOil):
            self.oilInBalloon += (self.pumpingPeriod * self.pumpRate)
            turned = True
            
            #calculating energy loss
            energyLost = (self.energyUsed(depth*1.45038)*(self.pumpingPeriod/60/60))/1000
            self.batteryPower -= energyLost
            self.propulsionPowerUsed += energyLost
        
        #corrects if goes over 1
        if (self.oilInBalloon >= self.maxOil):
            self.oilInBalloon = self.maxOil
            
        return turned
    
    def deflateBalloon(self, depth): #dive maneuver (down from surface) --- 100%->0%

        turned = False
        if (self.oilInBalloon > self.minOil):
            self.oilInBalloon -= (self.pumpingPeriod * self.pumpRate) #1.45038 psi per meter of seawater depth
            turned = True
            
            #NO energy loss!!
                    
        #corrects if goes under 0
        if(self.oilInBalloon <= self.minOil):
            self.oilInBalloon = self.minOil
                                            
        return turned
