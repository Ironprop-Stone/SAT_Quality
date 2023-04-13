import time 
import numpy as np 
import random
import time

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
    if 'AND' in gate_to_index.keys() and gate_type == gate_to_index['AND']:
        res = signals[0]
        for s in signals[1:]:
            res &= s
    elif 'NOT' in gate_to_index.keys() and gate_type == gate_to_index['NOT']:
        s_list = dec2list(signals[0], no_tt)
        for k, ele in enumerate(s_list):
            if ele == 0:
                s_list[k] = 1
            else:
                s_list[k] = 0
        res = list2dec(s_list)
    elif 'BUF' in gate_to_index.keys() and gate_type == gate_to_index['BUF']:
        res = signals[0]
    elif 'OR' in gate_to_index.keys() and gate_type == gate_to_index['OR']:
        res = signals[0]
        for s in signals[1:]:
            res |= s
    elif 'NAND' in gate_to_index.keys() and gate_type == gate_to_index['NAND']:
        res = signals[0]
        for s in signals[1:]:
            res &= s
        s_list = dec2list(res, no_tt)
        for k, ele in enumerate(s_list):
            if ele == 0:
                s_list[k] = 1
            else:
                s_list[k] = 0
        res = list2dec(s_list)
    elif 'NOR' in gate_to_index.keys() and gate_type == gate_to_index['NOR']:
        res = signals[0]
        for s in signals[1:]:
            res |= s
        s_list = dec2list(res, no_tt)
        for k, ele in enumerate(s_list):
            if ele == 0:
                s_list[k] = 1
            else:
                s_list[k] = 0
        res = list2dec(s_list)
    elif 'XOR' in gate_to_index.keys() and gate_type == gate_to_index['XOR']:
        res = signals[0]
        for s in signals[1:]:
            res ^= s
    else:
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

def simulator(x_data, PI_indexes, level_list, fanin_list, gate_to_index, tot_pts=16384, parallel_width=16, tot_time=-1):
    prob_1 = [0] * len(x_data)
    no_patterns = 0 
    start_time = time.time()
    while tot_time > 0 or no_patterns < tot_pts:
        if tot_time > 0 and time.time() - start_time > tot_time:
            break

        state = [-1] * len(x_data)
        # Initial FF state 
        for pi_idx in PI_indexes:
            state[pi_idx] = random.randint(0, int(pow(2, parallel_width)-1))
        
        # Simulation
        state = comb_prog(x_data, level_list, fanin_list, gate_to_index, parallel_width, state)
        
        # Statistic
        no_patterns += parallel_width
        for node_idx in range(len(x_data)):
            s_list = np.array(dec2list(state[node_idx], parallel_width))
            prob_1[node_idx] += (s_list == 1).sum()
            
    for node_idx in range(len(x_data)):
        prob_1[node_idx] /= no_patterns
        
    return prob_1, no_patterns
            
