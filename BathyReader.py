#!/usr/bin/env python
# coding: utf-8

#Created by: Lucille Shield


# Standard imports
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator
import numpy as np

##################################################################################
# This class enables reading bathymetry (ocean depth) data from a bathymetry file.
#
# The file is assumed to be in NetCDF format, typically from GEBCO:
#   https://www.gebco.net/data_and_products/gridded_bathymetry_data
#
# The supplied file can be the entire worldwide DB (huge!) or a subset.
##################################################################################
class bathymetryReader:

    # ---------------------------------------------------------
    # Constructor with filename
    # Loads the data & stores the grids in an interpolator
    # ---------------------------------------------------------
    def __init__(self, bathyFile):
        dataset = Dataset(bathyFile,'r')
 
        # Get the grids
        latGrid = dataset.variables['lat'][:] # lat grid
        lonGrid = dataset.variables['lon'][:] # lon grid
        elevationGrid = dataset.variables['elevation'][:] # elevation grid

        # Create interpolator on elevation
        self.elevInterp = RegularGridInterpolator((latGrid,lonGrid), elevationGrid)

    # ---------------------------------------------------------
    # Return the depth for the specified location
    # ---------------------------------------------------------
    def getDepth(self, lat, lon):

        # Interpolate elevation
        #elevation = self.elevInterp([lat, lon])
        
        #to debug
        try:
            elevation = self.elevInterp([lat, lon])
        except:
            print(lat)
            print(lon)
            raise Exception("Out of range")
        
        # Depth is negative elevation
        return -elevation


# In[ ]: