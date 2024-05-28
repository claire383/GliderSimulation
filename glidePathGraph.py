import matplotlib.pyplot as plt

#graphing important quantities over time
def plotter(t, d, e, b, p, plotName):
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
    ax1.plot(t, d, color="orange")
    ax2.plot(t, e, color="green")
    ax3.plot(t, b, color="blue")
    ax4.plot(t, p, color="magenta")

    ax1.invert_yaxis()
    ax1.set_title('Depth v.s. Time')
    ax1.set_xlabel('minutes')
    ax1.set_ylabel('meters')
    ax1.grid()

    ax2.set_title('Energy v.s. Time')
    ax2.set_xlabel('minutes')
    ax2.set_ylabel('kWh')
    ax2.grid()

    ax3.set_title('Buoyancy State v.s. Time')
    ax3.set_xlabel('minutes')
    ax3.set_ylabel('cubic centimeters')
    ax3.grid()

    ax4.set_title('Pitch Agle v.s. Time')
    ax4.set_xlabel('minutes')
    ax4.set_ylabel('radians')
    ax4.invert_yaxis()
    ax4.grid()

    plt.subplots_adjust(wspace = 0.4, hspace = 0.5)

    plt.savefig(plotName)


'''from OceanData import oceanData
from datetime import datetime

oceanInfo = oceanData('SoCalData+Sim/JuneSoCalHYCOM')

#sal, temp = oceanInfo.salAndTemp(datetime(2023, 6, 9, 0).timestamp(), 0, 33.3, 242.2)

#easting, northing = oceanInfo.currents(datetime(2023, 6, 11, 8, 18, 2).timestamp(), 317.3012361245012, 32.9219934695346, 360-118.40898715247707)
#easting, northing = oceanInfo.currents(datetime(2023, 6, 11, 8, 17, 2).timestamp(), 312.1149451865124, 32.92921848862886, 360-118.40007126874049)
easting, northing = oceanInfo.currents(datetime(2023, 6, 11, 8, 17, 2).timestamp(), 312.1149451865124, 32.92921848862886, 360-118.40007126874049)

print(northing)

import BathyReader

oceanInfo = BathyReader.bathymetryReader('SoCalData+Sim/gebco_2023_n33.4_s32.7_w-118.7_e-117.2.nc')
print(oceanInfo.getDepth(32.9219934695346, -118.40098715247707))'''