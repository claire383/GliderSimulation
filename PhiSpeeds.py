import numpy as np

def speedCalc(clA, clB, cdA, cdB):
    xVelParts = []
    zVelParts = []

    #in degrees
    thetas = []
    phis = []
    alphas = []

    angles = np.linspace(1, 20, 300)

    for a1 in angles:
        a = a1 * np.pi / 180 #converting to radians
        alphas.append(a1)
        
        cl = clA + clB * a
        cd = cdA + cdB * a**2

        theta = np.arctan(cd / cl)
        thetas.append(theta * 180 / np.pi)
        
        phis.append((theta * 180 / np.pi) - a1)
        
        velocityPart = np.sqrt((np.cos(theta)) / (cl))
        
        vx = velocityPart * np.cos(theta)
        vz = velocityPart * np.sin(theta)
        
        xVelParts.append(vx)
        zVelParts.append(vz)
                        
    return phis, xVelParts, zVelParts
    