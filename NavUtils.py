"""
 General purpose navigational utilities
"""

# Standard imports
import os
import math
import time
import datetime
import numpy as np
from scipy.spatial.transform import Rotation as sstr

# Approximate earth radius (meters)
# Use the mean of polar & equatorial radii
EARTH_POLAR_RADIUS = 6356800
EARTH_EQUATORIAL_RADIUS = 6378100 
EARTHR = np.mean([EARTH_POLAR_RADIUS, EARTH_EQUATORIAL_RADIUS]) #in meters

# Approx meters / deg of latitude
METERS_PER_DEGREE = EARTHR * np.pi/180

#########################################################################
# Degree-based trig functions
#########################################################################
def sind(theta): 
    return np.sin(np.deg2rad(theta))
def cosd(theta):
    return np.cos(np.deg2rad(theta))
def tand(theta):
    return np.tan(np.deg2rad(theta))

#########################################################################
# Degree-based inverse trig functions
#########################################################################
def asind(x):
    return np.rad2deg(np.arcsin(x))
def acosd(x):
    return np.rad2deg(np.arccos(x))
def atand(x):
    return np.rad2deg(np.arctan(x))
def atan2d(y, x):
    phi = np.rad2deg(np.arctan2(y, x))
    # Normalize to [0,360]
    if (phi < 0):
        phi = phi + 360
    return phi

#########################################################################
# Calculate the great circle distance (in meters) from
# the first supplied lat/lon point to the second
#
# All args expected in degrees
#
# Uses Sperical Law of Cosines for Approximation
#########################################################################
def distance(lat1, lon1,
             lat2, lon2):
    # Angular distance
    arg = sind(lat2) * sind(lat1) + cosd(lat2) * cosd(lat1) * cosd(lon2 - lon1)
    # NOTE: np.min used when arg is slightly larger than 1 (due to rounding error)
    phi = np.arccos(np.minimum(1, arg))  # radians

    # To distance
    return EARTHR * phi

#########################################################################
# Calculate the great circle bearing (in deg) from
# the first supplied lat/lon point to the second
#
# All args expected in degrees
#########################################################################
def bearing(lat1, lon1,
            lat2, lon2):
    num = cosd(lat2) * sind(lon2 - lon1)
    den = sind(lat2) * cosd(lat1) - cosd(lat2) * sind(lat1) * cosd(lon2 - lon1)
    return atan2d(num, den)

#########################################################################
# Propagate a geographic position by applying the specified
# direction and distance to the specified initial position.
#########################################################################
def projectPosition(lat1, lon1, # deg
                    direction,  # deg
                    distance):  # met

    # Angular Distance (deg)
    phi = np.rad2deg(distance / EARTHR)

    # Project latitude
    lat2 = asind(cosd(phi) * sind(lat1) +
                 sind(phi) * cosd(lat1) * cosd(direction))

    # Project longitude
    num = sind(phi) * sind(direction)
    den = cosd(phi) * cosd(lat1) - sind(phi) * sind(lat1) * cosd(direction)
    lon2 = lon1 + atan2d(num, den)

    # Normalize longitude to [-180,+180]
    if lon2 > 180:
        lon2 -= 360
    if lon2 >= 360:
        lon2 -= 360
    if lon2 <= -360:
        lon2 += 360

    return (lat2, lon2)

#########################################################################
# Propagate a geographic position by applying the specified
# distances in X and Y.
#
# Our convention for X,Y is that of a North-East-Down (NED) frame:
# - X is North
# - Y is East
# - Z is down
# Therefore X,Y are applied to latitude & longitude respectively
#########################################################################
def projectPositionXY(lat1, lon1,  # deg
                      dX, dY ):    # northing, easting: meters
    lat2 = lat1 + dX / METERS_PER_DEGREE
    # Mid-lat for meridan squeeze approximation
    latM = (lat1 + lat2) / 2.
    lon2 = lon1 + dY / METERS_PER_DEGREE / cosd(latM)

    return (lat2, lon2)

#########################################################################
# Propagate a geographic position by applying the specified
# velocity U,V components to the specified initial position
# for the specified period.
#
# We assume U,V are easterly and northerly respectively, following
# the convention used in ocean current models.
#########################################################################
def projectPositionUV(lat1, lon1,  # deg
                      u, v,        # easterly, northerly: m/s
                      dt):         # sec
    dX = v * dt  # northing
    dY = u * dt  # easting
    return projectPositionXY(lat1, lon1, dX, dY)

#########################################################################
# Convert the given lat/lon grid to Cartesian (X,Y)
# using a simple tangent-plane approximation
#########################################################################
def generateXYGrid(lat, lon):
    y = np.zeros_like(lat)
    x = np.zeros_like(lon)

    # Midpoint in lat & lon
    midLat = (min(lat) + max(lat)) / 2
    midLon = (min(lon) + max(lon)) / 2

    # This nested loop is inefficient: Lat,Lon are independent
    # But convenient for use of arbitrary XY conversion routines.
    for i in range(len(lat)):
        for j in range(len(lon)):
            (xx, yy) = latLon2XY(lat[i], lon[j],
                                 midLat, midLon)
            y[i] = yy
            x[j] = xx

    return (midLat, midLon, x, y)

#########################################################################
# Generate Cartesian X,Y from a specified lat/lon,
# given the midpoint
#########################################################################
def latLon2XY(lat, lon, midLat, midLon):
    y = (lat - midLat) * METERS_PER_DEGREE
    x = (lon - midLon) * METERS_PER_DEGREE * math.cos(math.radians(midLat))

    return x, y #might need to add parentheses back

#########################################################################
# Inverse of tha above:
# Generate Cartesian X,Y from a specified lat/lon,
# given the midpoint
#########################################################################
def xy2LatLon(x, y, midLat, midLon):
    lat = y / METERS_PER_DEGREE + midLat
    lon = x / (METERS_PER_DEGREE * math.cos(math.radians(midLat))) + midLon

    return (lat, lon)

#########################################################################
# Normalize an angle to the range [0,360]
#########################################################################
def norm360(theta):
    return (theta + 360.0) % 360.0

#########################################################################
# Rotate a vector given in body coordinates to inertial
#
# The supplied angles are the body orientation in inertial space:
#########################################################################
def body2Inertial( vBody,
                   roll, pitch, heading,
                   isDegrees=True ):  # else radians
    # Form rotation
    rot = sstr.from_euler('xyz',
                          [roll,pitch,heading],
                          degrees=isDegrees)
    # Apply to body vector
    vInertial = rot.apply(vBody)
    return vInertial

#########################################################################
# Rotate a vector given in inertial coordinates to body frame
#
# The supplied angles are the body orientation in inertial space
#########################################################################
def inertial2Body( vInertial,
                   roll, pitch, heading,
                   isDegrees=True ):
    # Form rotation & invert
    rot = (sstr.from_euler('xyz',
                           [roll,pitch,heading],
                           degrees=isDegrees)).inv()
    # Apply to inertial vector
    vBody = rot.apply(vInertial)
    return vBody

#########################################################################
# Find the shorter angular distance between two headings.
#   hdg1 - hdg2
#########################################################################
def deltaHeading( hdg1, hdg2 ):
    hdg1 = norm360(hdg1)
    hdg2 = norm360(hdg2)
    delta = hdg1 - hdg2
    # Go the short way 'round
    if( delta > 180 ):
        delta -= 360;
    if( delta < -180 ):
        delta += 360;
    return delta;