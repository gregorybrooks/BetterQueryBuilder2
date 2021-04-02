import pdb
import sys
sys.path.append("../")
import os
import json
from greedy_mover_distance import greedy_mover_distance
import numpy as np
import re
import math 
import statistics 
from collections import Counter



def get_request_doc_event_info(example_doc, nlp):
    """[This function takes a request document and computes the event type frequency and event type to keywords]

    Args:
        example_doc ([type]): [description]
        nlp ([type]): [description]

    Returns:
        [type]: [description]
    """
   
    event_types = [] 
    etype2keyword = {} 

    if 'isi-events' not in example_doc: 
        example_doc['isi-events'] = example_doc['events']
    
    
    for event in example_doc['isi-events']:
        patients = []
        agents = []
        anchors = []
    
        event_types.append(event['eventType'])
        etype2keyword.setdefault(event['eventType'], [])        
        
        anchors.append(event['anchor']['string'])        
        
        for patient in event['patients']:
            patients.append(patient['string'])        
        
        for agent in event['agents']:
            agents.append(agent['string'])    
        
        keywords = agents + patients #+ anchors 
        etype2keyword[event['eventType']]+=keywords
        
    d = Counter(event_types)
    event_type_tf = []
    
    for k, v in d.items():
        event_type_tf.append((k, v))
    event_type_tf = sorted(event_type_tf, key=lambda x: x[1], reverse=True)    
    return event_type_tf, etype2keyword

