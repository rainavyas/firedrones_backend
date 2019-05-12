import requests
import numpy as np
from drone_functions import *
from munkres import Munkres

def do_all():
    m = Munkres()

    Drones_URL = "https://us-central1-firedrones-19.cloudfunctions.net/getDrones"
    Events_URL = "https://us-central1-firedrones-19.cloudfunctions.net/getIncidents"
    Change_Drones_URL = "https://us-central1-firedrones-19.cloudfunctions.net/changeDrones"
    Change_Incident_URL = "https://us-central1-firedrones-19.cloudfunctions.net/changeIncident2"

    BASE_LIST = [(51.5,0.12), (52.0, -1.0)]
    #define header for all http putting
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        }

    #get drone data
    r = requests.get(url = Drones_URL)
    drones_list = r.json()

    #get events data
    r = requests.get(url = Events_URL)
    events_list = r.json()

    #find number of events
    pending_events = [event for event in events_list if(event['processed']==1 or event['processed']==2)]
    num_events = len(pending_events)

    #find number of drones
    available_drones = [drone for drone in drones_list if drone['isRecall']==0]
    recalled_drones = [drone for drone in drones_list if drone['isRecall']==1]
    num_drones = len(available_drones)

    #create empty square matrix with padding
    size = max(num_drones, num_events)
    a = np.zeros(shape=(size,size))

    # fill in matrix with metric = distance/severity^2  ... 10000 for dummies
    for i, drone in enumerate(available_drones):
        for j, event in enumerate(pending_events):
            if(i<num_drones or j<num_events):
                a[i,j] = metric(drone, event)

    # Hungarian algorithm for assignment problem
    indexes = m.compute(a)

    # list of available drone allocations
    drone_allocations = [tup for tup in indexes if (tup[0]<num_drones and tup[1]<num_events)]

    # update drone database and incident database
    MIN_DISTANCE = 0.05
    for allocation in drone_allocations:
        curr_drone = available_drones[allocation[0]]
        assigned_event = pending_events[allocation[1]]

        current_location = (curr_drone["current_pos"]["_latitude"], curr_drone["current_pos"]["_longitude"])
        destination_location = (assigned_event["location"]["_latitude"], assigned_event["location"]["_longitude"])
        event_id = assigned_event["id"]
        speed = curr_drone["speed"]
        new_pos = interpolate_position(current_location, destination_location, speed)
        angle_distance = find_distance(new_pos, destination_location)
        print(angle_distance)

        if angle_distance < MIN_DISTANCE:
            """ Drone has reached destination"""

            payload = "{\"drone_id\" : \""+curr_drone["id"]+"\",\"d_lon\": "+str(new_pos[1])+",\"d_lat\": "+str(new_pos[0])+",\"event_id\" : \"\" ,\"speed\": "+str(curr_drone["speed"])+",\"capacity\": "+str(curr_drone["capacity"])+",\"isRecall\" : "+str(curr_drone["isRecall"]).lower()+"}"
            response = requests.request("PUT", Change_Drones_URL, data=payload, headers=headers)

            payload = "{\"processed\": 3,\"severity\": "+str(assigned_event["severity"])+",\"incident_id\": \""+str(assigned_event["id"])+"\"}"
            response = requests.request("PUT", Change_Incident_URL, data=payload, headers=headers)

        else:
            """ Drone is still travelling to event"""

            payload = "{\"drone_id\" : \""+curr_drone["id"]+"\",\"d_lon\": "+str(new_pos[1])+",\"d_lat\": "+str(new_pos[0])+",\"event_id\" : \""+event_id+"\" ,\"speed\": "+str(curr_drone["speed"])+",\"capacity\": "+str(curr_drone["capacity"])+",\"isRecall\" : "+str(curr_drone["isRecall"]).lower()+"}"
            response = requests.request("PUT", Change_Drones_URL, data=payload, headers=headers)

            payload = "{\"processed\": 2,\"severity\": "+str(assigned_event["severity"])+",\"incident_id\": \""+str(assigned_event["id"])+"\"}"
            response = requests.request("PUT", Change_Incident_URL, data=payload, headers=headers)


    # Drones not allocated to any events/recalled to be made unassigned to events
    deployed_drone_ids = [available_drones[allocation[0]]["id"] for allocation in drone_allocations]
    for drone in drones_list:
        current_location = (drone["current_pos"]["_latitude"], drone["current_pos"]["_longitude"])
        speed = drone["speed"]

        distance_list = [find_distance(current_location, base) for base in BASE_LIST]
        min_value = min(distance_list)
        min_index = distance_list.index(min_value)
        BASE_LOCATION = BASE_LIST[min_index]
        new_pos = interpolate_position(current_location, BASE_LOCATION, speed)
        if not (drone["id"] in deployed_drone_ids):
            payload = "{\"drone_id\" : \""+drone["id"]+"\",\"d_lon\": "+str(new_pos[1])+",\"d_lat\": "+str(new_pos[0])+",\"event_id\" : \"\" ,\"speed\": "+str(drone["speed"])+",\"capacity\": "+str(drone["capacity"])+",\"isRecall\" : "+str(drone["isRecall"]).lower()+"}"
            response = requests.request("PUT", Change_Drones_URL, data=payload, headers=headers)
        print(find_distance(current_location, BASE_LOCATION))
    # Events with drones no longer deployed to be made process = 1
    assigned_event_ids = [pending_events[allocation[1]]["id"] for allocation in drone_allocations]
    for event in pending_events:
        if not (event["id"] in assigned_event_ids):
            payload = "{\"processed\": 1,\"severity\": "+str(event["severity"])+",\"incident_id\": \""+str(event["id"])+"\"}"
            response = requests.request("PUT", Change_Incident_URL, data=payload, headers=headers)
