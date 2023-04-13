'''
Utility functions for Look-up-table
Author: Stone
'''
import time
from numpy.random import randint
import copy
from collections import Counter

def read_file(file_name):
    f = open(file_name, "r")
    data = f.readlines()
    return data

def list2dec(lst):
    tmp_str = ''
    for ele in lst:
        tmp_str += str(ele)
    return int(tmp_str, 2)

def feature_gen_init(lines): 
    node2idx = {}
    x_data = []
    fanin_list = []
    fanout_list = []
    
    # Find node names 
    for line in lines: 
        if 'INPUT' in line:
            node_name = line.split("(")[1].split(")")[0]
            node2idx[node_name] = len(x_data)
            x_data.append([node_name, 'PI'])
        elif 'LUT ' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            func = tmp_line.split('LUT0x')[-1].split('(')[0]
            func = '0x' + func
            node2idx[node_name] = len(x_data)
            x_data.append([node_name, func])
        elif 'gnd' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            func = 'GND'
            node2idx[node_name] = len(x_data)
            x_data.append([node_name, func])
        elif 'vdd' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            func = 'VDD'
            node2idx[node_name] = len(x_data)
            x_data.append([node_name, func])
            
    no_nodes = len(x_data)
    for idx in range(no_nodes):
        fanin_list.append([])
        fanout_list.append([])
            
    for line in lines:
        if 'LUT ' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            dst_idx = node2idx[node_name]
            fanin_line = tmp_line.split('(')[-1].split(')')[0]
            fanin_name_list = fanin_line.split(',')
            for fanin_name in fanin_name_list:
                fanin_idx = node2idx[fanin_name]
                fanin_list[dst_idx].append(fanin_idx)
                fanout_list[fanin_idx].append(dst_idx)
        elif 'gnd' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            dst_idx = node2idx[node_name]
            fanin_list[dst_idx] = []
        elif 'vdd' in line:
            tmp_line = line.replace(' ', '')
            node_name = tmp_line.split('=')[0]
            dst_idx = node2idx[node_name]
            fanin_list[dst_idx] = []
                
    return x_data, fanin_list, fanout_list

def convert_cnf(data, fanin_list, po_idx):
    cnf = []
    for idx, x_data_info in enumerate(data): 
        if x_data_info[1] == '':
            continue
        if x_data_info[1] == 'gnd':
            cnf.append([-1 * (idx + 1)])
            continue
        if x_data_info[1] == 'vdd':
            cnf.append([1 * (idx + 1)])
            continue
        tt_len = int(pow(2, len(fanin_list[idx])))
        func = bin(int(x_data_info[1], 16))[2:].zfill(tt_len)
        # print(x_data_info[1], tt_len)
        
        for func_idx, y_str in enumerate(func):
            y = 1 if int(y_str) == 1 else -1
            clause = [y * (idx+1)]
            
            mask_val = tt_len - func_idx - 1
            mask_list = bin(mask_val)[2:].zfill(len(fanin_list[idx]))
            for k, ele in enumerate(mask_list):
                var = fanin_list[idx][-1 * (k+1)] + 1
                var = var if int(ele) == 0 else (-1 * var)
                clause.append(var)
            cnf.append(clause)
    cnf.append([po_idx + 1])
            
    return cnf                       

def get_pi_po(fanin_list, fanout_list): 
    pi_list = []
    po_list = []
    for idx in range(len(fanin_list)):
        if len(fanin_list[idx]) == 0 and len(fanout_list[idx]) > 0:
            pi_list.append(idx)
    for idx in range(len(fanout_list)):
        if len(fanout_list[idx]) == 0 and len(fanin_list[idx]) > 0:
            po_list.append(idx)
    return pi_list, po_list

def get_level(x_data, fanin_list, fanout_list):
    bfs_q = []
    x_data_level = [-1] * len(x_data)
    max_level = 0
    for idx, x_data_info in enumerate(x_data):
        if len(fanin_list[idx]) == 0:
            bfs_q.append(idx)
            x_data_level[idx] = 0
    while len(bfs_q) > 0:
        idx = bfs_q[-1]
        bfs_q.pop()
        tmp_level = x_data_level[idx] + 1
        for next_node in fanout_list[idx]:
            if x_data_level[next_node] < tmp_level:
                x_data_level[next_node] = tmp_level
                bfs_q.insert(0, next_node)
                if x_data_level[next_node] > max_level:
                    max_level = x_data_level[next_node]
    level_list = []
    for level in range(max_level+1):
        level_list.append([])
        
    if -1 in x_data_level:
        print('Wrong')
        raise
    else:
        if max_level == 0:
            level_list = [[]]
        else:
            for idx in range(len(x_data)):
                level_list[x_data_level[idx]].append(idx)
    return level_list

def parse_bench(bench_file):
    data = read_file(bench_file)
    data, fanin_list, fanout_list = feature_gen_init(data)
    return data, fanin_list, fanout_list
    
def parse_bench_cnf(bench_file):
    data = read_file(bench_file)
    data, fanin_list, fanout_list = feature_gen_init(data)
    pi_list, po_list = get_pi_po(fanin_list, fanout_list)
    no_var = len(data)
    
    cnf = convert_cnf(data, fanin_list, po_list[0])
    return cnf, no_var

def partition(data, fanin_list, fanout_list, level_list, partition_level): 
    low_data = []
    org2low = {}
    low_fanin_list = []
    low_fanout_list = []
    high_data = []
    org2high = {}
    high_fanin_list = []
    high_fanout_list = []
    
    for level in range(len(level_list)):
        if level <= partition_level: 
            for org_idx in level_list[level]:
                low_idx = len(low_data)
                org2low[org_idx] = low_idx
                low_data.append(low_idx)
        if level >= partition_level:
            for org_idx in level_list[level]:
                high_idx = len(high_data)
                org2low[org_idx] = high_idx
                high_data.append(high_idx)
    
def random_pattern_generator(no_PIs):
    vector = [0] * no_PIs

    vector = randint(2, size=no_PIs)
    return vector

def logic(gate_type, signals, gate_to_index):
    if '0x' in gate_type:  # LUT
        lut_value = int(gate_type, 16)
        len_lut = int(pow(2, len(signals)))
        lut_list = bin(lut_value)[2:]
        lut_list = lut_list.zfill(len_lut)
        lut_list = lut_list[::-1]
        index_list = signals[::-1]
        index = list2dec(index_list)
        res = int(lut_list[index])
        return res
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

def convert_key_to_number(x_data, gate_to_index, no_key_length):
    for idx, x_data_info in enumerate(x_data):
        if '0x' in x_data_info[1]:
            lut_key = x_data_info[1][2:]
            while len(lut_key) < no_key_length:
                lut_key += lut_key
            assert len(lut_key) == no_key_length 
            lut_value = int(lut_key, 16)
            x_data[idx][1] = lut_value
        else:
            x_data[idx][1] = gate_to_index[x_data_info[1]]

    return x_data

def convert_key_to_index(x_data, gate_to_index, lut_to_index):
    for idx, x_data_info in enumerate(x_data):
        if '0x' in x_data_info[1]:
            x_data[idx][1] = lut_to_index[x_data_info[1]]
        else:
            x_data[idx][1] = gate_to_index[x_data_info[1]]

    return x_data

def gen_full_edge_index(fanin_list, no_fanin):
    edge_index = []
    for idx in range(len(fanin_list)):
        if len(fanin_list[idx]) == 0:
            continue
        for k in range(no_fanin):
            fanin_idx = fanin_list[idx][k % len(fanin_list[idx])]
            edge_index.append([fanin_idx, idx])

    return edge_index

def gen_full_fanin(fanin_list):
    new_fanin_list = []
    for idx in range(len(fanin_list)):
        if len(fanin_list[idx]) == 0:
            new_fanin_list.append([-1, -1])
        elif len(fanin_list[idx]) == 1:
            new_fanin_list.append([fanin_list[idx][0], fanin_list[idx][0]])
        else: 
            new_fanin_list.append(fanin_list[idx])
    return new_fanin_list
