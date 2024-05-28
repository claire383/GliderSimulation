# ----------------------------------------------------------
# Plot data from a Carina "crash" log.
# ----------------------------------------------------------

# Global imports
import sys
import numpy as np
import matplotlib.pyplot as plot

# Local imports
import CrashReader as cr

# ------------------------------------------------------------
# App Main Entry Point
# ------------------------------------------------------------

'''# Sanity check - must supply filename
nArgs = len(sys.argv)
if nArgs < 2 :
    print(' - Must supply data filename')
    sys.exit()
fileName = sys.argv[1]'''

#stopped at 240
fileName = 'SoCalData+Sim/SoCalCrashLogsMarch2024/c002-265.crash.log'

# Extract the data
print(' - Reading: %s' % fileName)
(depthTime, depth, attitudeTime, pitch, roll, heading, vbdTime, vbd) = cr.readCrashLog( fileName )
print(' - File Read')
print('     Depth record count: %d' % len(depthTime))
print('     Attitude record count: %d' % len(attitudeTime))
print('     VBD record count: %d' % len(vbdTime))

# Normalize times to their starting points (generate elapsed time)
depthTime = np.array(depthTime) - depthTime[0]
attitudeTime = np.array(attitudeTime) - attitudeTime[0]
vbdTime = np.array(vbdTime) - vbdTime[0]
# Convert times from elapsed sec to elapsed minutes to match "Snoopy" plots
depthTime /= 60.
attitudeTime /= 60.
vbdTime /= 60.

# --------------------------------------------------------------------------
# Plot it up!
# --------------------------------------------------------------------------

# First figure - depth alone
depthFig = plot.figure("Depth")
plot.plot(depthTime, depth)
plotObj = plot.gca()
plotObj.invert_yaxis()  # plot depth positive down
plotObj.set_title('Depth vs Time')
plotObj.grid(which='both',axis='both')
plotObj.set(xlabel='minutes')
plotObj.set(ylabel='meters')

# Second figure - attitude
attFig,attPlots = plot.subplots(2,1)
attFig.suptitle('Attitude')
# Pitch & roll
pitchRollPlot = attPlots[0]
pitchRollPlot.plot(attitudeTime,pitch,color='r',label='pitch')
pitchRollPlot.plot(attitudeTime,roll,color='b',label='roll')
pitchRollPlot.set_title('Pitch & Roll vs Time')
pitchRollPlot.set(xlabel="minutes")
pitchRollPlot.set(ylabel="deg")
pitchRollPlot.grid(which='both',axis='both')
pitchRollPlot.legend(loc="upper right")
# Heading
headingPlot = attPlots[1]
headingPlot.scatter(attitudeTime,heading)
headingPlot.set_title('Heading vs Time')
headingPlot.set(xlabel="minutes")
headingPlot.set(ylabel="deg")
headingPlot.grid(which='both',axis='both')
plot.subplots_adjust(hspace=1)

# Third figure - VBD alone
vbdFig = plot.figure("VBD")
plot.plot(vbdTime, vbd)
plotObj = plot.gca()
plotObj.set_title('VBD vs Time')
plotObj.grid(which='both',axis='both')
plotObj.set(xlabel='minutes')
plotObj.set(ylabel='cc')

# Show plots
plot.show(block=False)
input(' - Hit CR to exit')
        
print('\n === DONE === \n')