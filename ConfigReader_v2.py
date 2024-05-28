#!/usr/bin/python3

# ------------------------------------------------------------------
# This class handles data supplied in "config file" format
#
# This format enables specification of data in key=value pairs
#
# Note:
# - Any line beginning with "#" is ignored
# - A "#" anywhere in a line marks the rest of the line as ignored
# - Data is organized in Sections, with a section delineated by:
#   [ThisSection]
#
# Once the file is read, data from sections can be requested and
# returned to the caller in 1 of 3 forms:
# 1. As a character string
# 2. As an integer
# 3. As a floating point number
#
# If the requested key doesn't exist in the requested section,
# or if the requested section doesn't exist, an error is returned
# If the key requested exists but cannot be cast into the specified
# numerical form, an error is returned.
#
# An ERROR is identified as the Python value "None"
# ------------------------------------------------------------------

import os
import configparser

class configReader_v2:
	
# ------------------------------------------------------------------
# Constructor
# ------------------------------------------------------------------
    def __init__(self):
        return

    # --------------------------------------------------------------
    # Load file & parse keys/values
    # --------------------------------------------------------------
    def loadFile(self,filename):

	# Does file exist?
        if not os.path.exists(filename):
            print('ERROR: file %s not found'%filename)
            return False

        # Open & read file 
        
        self.config = configparser.ConfigParser()
        self.config.read(filename)

        return True

    # --------------------------------------------------------------
    # Get value associated with specified section & key as a string
    # --------------------------------------------------------------
    def getString(self,section,key):
		
	## try to get value as string
        try:
            line = self.config[section][key]
     
            if '#' in line:
                
                line = line.split('#')[0]
                line = line.replace(' ','')
                
            return line
		
	## return error if value specified not found
        except: 
            print('ERROR: section/key %s/%s combination not found'%(section,key))
            return None

    # --------------------------------------------------------------
    # Get value associated with specified section & key as an int
    # --------------------------------------------------------------
    def getInt(self,section,key):

	# Get value as a string
        str = self.getString(section,key)

	# Return None if unable to get value as string
        if str is None:
            return None

        # Convert string to integer value
        else:
            try: 
                return int(str) 
            # Return error if unable to convert value to integer
            except: 
                print('ERROR: unable to convert string %s to integer value'%str)
                return None

    # --------------------------------------------------------------
    # Get value associated with specified section & key as a float
    # --------------------------------------------------------------
    def getFloat(self,section,key):

	# Get value as a string
        str = self.getString(section,key)

	# Return None if unable to get value as string
        if str is None:
            return None

        # Convert string to float value
        else:
            try: 
                return float(str)
	    # return error if unable to convert value to integer
            except: 
                print('ERROR: unable to convert string %s to float value'%str)
                return None
            
    def getIntList(self,section,key):

	# Get value as a string
        str = self.getString(section,key)

	# Return None if unable to get value as string
        if str is None:
            return None

        # Convert string to integer value
        else:
            try:
                str = str[1:len(str)-1]
                array = []
                
                for i in range(str.count(',')):
                    n = str.find(',')
                    str1 = str[0:n]
                    array.append(int(str1))
                    
                    str = str[n+1:]
                    
                array.append(int(str))
                    
                return array
            # Return error if unable to convert value to integer
            except: 
                print('ERROR: unable to convert string %s to integer value'%str)
                return None