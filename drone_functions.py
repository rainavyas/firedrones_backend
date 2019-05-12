from numpy import *
from math import atan2

TIME = 2
R = 6371


def distance(location_1, location_2):
    """ Haversine Formulae """
    lat_1 = location_1[0]*pi/180
    long_1 = location_1[1]*pi/180
    lat_2 = location_2[0]*pi/180
    long_2 = location_2[1]*pi/180

    a = sin((lat_2-lat_1)/2)**2 + cos(lat_1)*cos(lat_2)*sin((long_2-long_1)/2)**2
    c = 2*atan2(sqrt(a), sqrt(1-a))
    d = R*c
    return d


def metric(drone, event):
    current_location = (drone["current_pos"]["_latitude"], drone["current_pos"]["_longitude"])
    event_location = (event["location"]["_latitude"], event["location"]["_longitude"])
    severity = event["severity"]
    value = distance(current_location,event_location)/severity**2
    return value



def interpolate_position(tup_1, tup_2, speed):
    tup_1 = array(tup_1)
    difference = [tup_2[0]-tup_1[0], tup_2[1]-tup_1[1]]
    direction = [float(j)/sum([i**2 for i in difference])**0.5 for j in difference]
    direction = array(direction)
    magnitude = (speed*TIME)*180/(R*1000*pi)
    next_position = tup_1 + magnitude*direction
    return(next_position)

def find_distance(tup_1, tup_2):
    tup_1 = array(tup_1)
    difference = [tup_2[0]-tup_1[0], tup_2[1]-tup_1[1]]
    distance = sqrt((difference[0]**2)+ (difference[0]**2))
    return distance
