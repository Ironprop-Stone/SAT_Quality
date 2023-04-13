import time
from numpy.random import randint
import copy
from collections import Counter
import numpy as np

def decode_mig_xdata(x_data, gate_to_index):
    for idx in range(len(x_data)):
        if x_data[idx][1] == 'PI':
            x_data[idx][1] = gate_to_index['PI']
        elif x_data[idx][1] == 'GND': 
            x_data[idx][1] = gate_to_index['GND']
        elif x_data[idx][1] == 'VDD': 
            x_data[idx][1] = gate_to_index['VDD']
        elif x_data[idx][1] == '0x1': 
            x_data[idx][1] = gate_to_index['NOT']
        elif x_data[idx][1] == '0x2':
            x_data[idx][1] = gate_to_index['BUF']
        else:
            x_data[idx][1] = gate_to_index['MAJ']
    return x_data

def random_pattern_generator(no_PIs):
    vector = [0] * no_PIs

    vector = randint(2, size=no_PIs)
    return vector

def logic(gate_type, signals, gate_to_index):
    if 'NOT' in gate_to_index.keys() and gate_type == gate_to_index['NOT']:  # NOT
        for s in signals:
            if s == 1:
                return 0
            else:
                return 1

    elif 'BUF' in gate_to_index.keys() and gate_type == gate_to_index['BUF']:  # BUFF
        for s in signals:
            return s

    elif 'MAJ' in gate_to_index.keys() and gate_type == gate_to_index['MAJ']:  # MAJ
        logic_1_cnt = np.sum(signals)
        if logic_1_cnt > len(signals) / 2:
            return 1
        else:
            return 0
    
    else:
        print(gate_to_index)
        raise 'Unknown gate_type: {}'.format(gate_type)
        
def simulator(x_data, PI_indexes, level_list, fanin_list, gate_to_index, num_patterns=15000, tot_time=-1):
    '''
       Logic simulator for MIG
       Modified by Stone 14-11-2022
       '''
    state = [0] * len(x_data)
    y1 = [0] * len(x_data)
    pattern_count = 0
    if tot_time == -1:
        tot_pts = min(num_patterns, 10 * pow(2, len(PI_indexes)))

    start_time = time.time()
    while tot_time > 0 or pattern_count < tot_pts:
        if tot_time > 0 and time.time() - start_time > tot_time:
            break
        
        input_vector = random_pattern_generator(len(PI_indexes))
        for j, pi_idx in enumerate(PI_indexes):
            state[pi_idx] = input_vector[j]
            j = j + 1
        for idx in range(len(x_data)):
            if x_data[idx][1] == gate_to_index['GND']:
                state[idx] = 0
            elif x_data[idx][1] == gate_to_index['VDD']:
                state[idx] = 1

        for level in range(1, len(level_list), 1):
            for node_idx in level_list[level]:
                source_signals = []
                for pre_idx in fanin_list[node_idx]:
                    source_signals.append(state[pre_idx])
                if len(source_signals) > 0:
                    gate_type = x_data[node_idx][1]
                    state[node_idx] = logic(gate_type, source_signals, gate_to_index)
                    
        for node_idx in range(len(x_data)):
            if state[node_idx] == 1:
                y1[node_idx] = y1[node_idx] + 1

        pattern_count = pattern_count + 1
        # if pattern_count % 10000 == 0:
        #     print("pattern count = {:}k".format(int(pattern_count / 1000)))
    
    for i, _ in enumerate(y1):
        y1[i] = y1[i] / pattern_count

    return y1
