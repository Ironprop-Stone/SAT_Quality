import time
import random
import copy
from collections import Counter
import numpy as np

def dec2list(num, no_PIs):
    res = []
    bin_num = bin(num)[2:].zfill(no_PIs)
    for ele in bin_num:
        res.append(int(ele))
    return res

def list2dec(lst):
    tmp_str = ''
    for ele in lst:
        tmp_str += str(ele)
    return int(tmp_str, 2)

def logic(gate_type, signals, no_tt, gate_to_index):
    if -1 in signals:
        return -1
    elif 'NOT' in gate_to_index.keys() and gate_type == gate_to_index['NOT']:
        s_list = dec2list(signals[0], no_tt)
        s_list = np.array(s_list)
        s_list[s_list == 0] = 2
        s_list[s_list == 1] = 0
        s_list[s_list == 2] = 1
        res = list2dec(s_list)
    elif 'BUF' in gate_to_index.keys() and gate_type == gate_to_index['BUF']:
        res = signals[0]
    elif 'MAJ' in gate_to_index.keys() and gate_type == gate_to_index['MAJ']:  # MAJ
        s_list = [] 
        for s in signals:
            if len(s_list) == 0:
                s_list = np.array(dec2list(s, no_tt))
            else:
                s_list += np.array(dec2list(s, no_tt))
        s_list = s_list.astype(np.float32)
        s_list /= len(signals)
        s_list[s_list >= 0.5] = 1
        s_list[s_list < 0.5] = 0
        s_list = s_list.astype(np.int32)
        res = list2dec(s_list)
    else:
        print(gate_to_index)
        raise('Unsupport Gate Type: {:}'.format(gate_type))
    
    return res

def comb_prog(x_data, level_list, fanin_list, gate_to_index, parallel_width, state):
    for level in range(1, len(level_list), 1):
        for node_idx in level_list[level]:
            gate_type = x_data[node_idx][1]
            source_signals = []
            for pre_idx in fanin_list[node_idx]:
                source_signals.append(state[pre_idx])
            if len(source_signals) > 0:
                res = logic(gate_type, source_signals, parallel_width, gate_to_index)
                state[node_idx] = res
    return state

def pa_simulator(x_data, PI_indexes, level_list, fanin_list, gate_to_index, num_patterns=10000, width=16):
    prob_1 = [0] * len(x_data)
    no_patterns = 0
    while no_patterns < num_patterns:
        state = [-1] * len(x_data)
        for pi_idx in PI_indexes:
            state[pi_idx] = random.randint(0, int(pow(2, width)-1))
        for idx in range(len(x_data)):
            if x_data[idx][1] == gate_to_index['GND']:
                state[idx] = list2dec([0] * width)
            elif x_data[idx][1] == gate_to_index['VDD']:
                state[idx] = list2dec([1] * width)
            
        state = comb_prog(x_data, level_list, fanin_list, gate_to_index, width, state)

        # Statistic
        no_patterns += width
        for node_idx in range(len(x_data)):
            s_list = np.array(dec2list(state[node_idx], width))
            prob_1[node_idx] += (s_list == 1).sum()
    
    for node_idx in range(len(x_data)):
        prob_1[node_idx] /= no_patterns

    return prob_1