'''
Utility functions for circuit: including random pattern generation, logic simulator, \
    reconvergence identification, 
'''
import time
from numpy.random import randint
import copy
from collections import Counter

def dec2list(num, no_PIs):
    res = []
    bin_num = bin(num)[2:].zfill(no_PIs)
    for ele in bin_num:
        res.append(int(ele))
    return res

def read_file(file_name):
    f = open(file_name, "r")
    data = f.readlines()
    return data

def random_pattern_generator(no_PIs):
    vector = [0] * no_PIs

    vector = randint(2, size=no_PIs)
    return vector

def logic(gate_type, signals, gate_to_index):
    if 'AND' in gate_to_index.keys() and gate_type == gate_to_index['AND']:  # AND
        for s in signals:
            if s == 0:
                return 0
        return 1

    elif 'NAND' in gate_to_index.keys() and gate_type == gate_to_index['NAND']:  # NAND
        for s in signals:
            if s == 0:
                return 1
        return 0

    elif 'OR' in gate_to_index.keys() and gate_type == gate_to_index['OR']:  # OR
        for s in signals:
            if s == 1:
                return 1
        return 0

    elif 'NOR' in gate_to_index.keys() and gate_type == gate_to_index['NOR']:  # NOR
        for s in signals:
            if s == 1:
                return 0
        return 1

    elif 'NOT' in gate_to_index.keys() and gate_type == gate_to_index['NOT']:  # NOT
        for s in signals:
            if s == 1:
                return 0
            else:
                return 1

    elif 'BUF' in gate_to_index.keys() and gate_type == gate_to_index['BUF']:  # BUFF
        for s in signals:
            return s

    elif 'XOR' in gate_to_index.keys() and gate_type == gate_to_index['XOR']:  # XOR
        z_count = 0
        o_count = 0
        for s in signals:
            if s == 0:
                z_count = z_count + 1
            elif s == 1:
                o_count = o_count + 1
        if z_count == len(signals) or o_count == len(signals):
            return 0
        return 1

def reverse_logic(gate_type, signal, gate_to_index):
    if 'AND' in gate_to_index.keys() and gate_type == gate_to_index['AND']:  # AND
        if signal == 0:
            return 3
        elif signal == 3 or signal == 4:
            return 3
        elif signal == 1:
            return 1
    elif 'NOT' in gate_to_index.keys() and gate_type == gate_to_index['NOT']:  # NOT
        if signal == 0:
            return 1
        elif signal == 1:
            return 0
        elif signal == 3:
            return 4
        elif signal == 4:
            return 3

def simulator(x_data, PI_indexes, level_list, fanin_list, gate_to_index, patterns=[]):
    '''
       Logic simulator
       Modified by Stone 27-09-2021
       ...
       Parameters:
           x_data : list(list((str, int, int))), the node feature matrix with shape [num_nodes, num_node_features], the current dimension of num_node_features is 3, wherein 0th - node_name defined in bench (str); 1st - integer index for the gate type; 2nd - logic level; 3rd - C1, 4th - C0, 5th - Obs.
           level_list: logic levels
           fanin_list: the fanin node indexes for each node
           fanout_list: the fanout node indexes for each node
       Return:
           y_data : simualtion result
       '''
    y = [0] * len(x_data)
    y1 = [0] * len(x_data)

    start_time = time.time()
        
    if len(patterns) == 0:
        input_vector = random_pattern_generator(len(PI_indexes))
    else:
        input_vector = patterns
    j = 0
    for i in PI_indexes:
        y[i] = input_vector[j]
        j = j + 1

    for level in range(1, len(level_list), 1):
        for node_idx in level_list[level]:
            source_signals = []
            for pre_idx in fanin_list[node_idx]:
                source_signals.append(y[pre_idx])
            if len(source_signals) > 0:
                gate_type = x_data[node_idx][1]
                y[node_idx] = logic(gate_type, source_signals, gate_to_index)

    return y

def mask_simulator(x_data, PI_indexes, level_list, fanin_list, mask_list, gate_to_index, num_patterns=15000):
    '''
       Logic simulator
       Modified by Stone 27-09-2021
       Modified by Stone 23-01-2022: support node mask
       ...
       Parameters:
           x_data : list(list((str, int, int))), the node feature matrix with shape [num_nodes, num_node_features], the current dimension of num_node_features is 3, wherein 0th - node_name defined in bench (str); 1st - integer index for the gate type; 2nd - logic level; 3rd - C1, 4th - C0, 5th - Obs.
           level_list: logic levels
           fanin_list: the fanin node indexes for each node
           fanout_list: the fanout node indexes for each node
       Return:
           y_data : simualtion result
       '''
    y = [0] * len(x_data)
    y1 = [0] * len(x_data)
    pattern_count = 0
    success_count = 0
    no_of_patterns = min(num_patterns, 10 * pow(2, len(PI_indexes)))

    # print('[INFO] Begin simulation')
    while pattern_count < no_of_patterns and success_count < 5000:
        input_vector = random_pattern_generator(len(PI_indexes))
        failed = False

        j = 0
        for i in PI_indexes:
            if mask_list[i] != -1:
                y[i] = mask_list[i]
            else:
                y[i] = input_vector[j]
            j = j + 1

        for level in range(1, len(level_list), 1):
            if failed:
                break
            for node_idx in level_list[level]:
                if failed:
                    break
                source_signals = []
                for pre_idx in fanin_list[node_idx]:
                    source_signals.append(y[pre_idx])
                if len(source_signals) > 0:
                    gate_type = x_data[node_idx][1]
                    tmp_y = logic(gate_type, source_signals, gate_to_index)
                    if mask_list[node_idx] == -1:
                        y[node_idx] = tmp_y
                    elif mask_list[node_idx] != tmp_y:
                        failed = True
                        break
                    else:
                        y[node_idx] = tmp_y

        pattern_count = pattern_count + 1
        if not failed:
            success_count += 1
            for idx, x_data_info in enumerate(x_data):
                y1[idx] += y[idx]
        
    if success_count > 0:
        for i, _ in enumerate(y1):
            y1[i] = y1[i] / success_count
    success_ratio = success_count / pattern_count

    return success_count, y1, success_ratio

def mask_simulator_erg(x_data, PI_indexes, level_list, fanin_list, mask_list, gate_to_index):
    y = [0] * len(x_data)
    y1 = [0] * len(x_data)
    pattern_count = 0
    success_count = 0
    no_of_patterns = int(pow(2, len(PI_indexes)))
    # print('No of Patterns: {:}'.format(no_of_patterns))
    # print('No of Nodes: {:} '.format(len(x_data)))

    # print('[INFO] Begin simulation')
    for pattern_idx in range(no_of_patterns):
        # if pattern_idx % 10000 == 0: 
        #     print('# Patterns: {:}k'.format(int(pattern_idx / 1000)))
        input_vector = dec2list(pattern_idx, len(PI_indexes))
        failed = False

        j = 0
        for i in PI_indexes:
            if mask_list[i] != -1:
                y[i] = mask_list[i]
            else:
                y[i] = input_vector[j]
            j = j + 1

        for level in range(1, len(level_list), 1):
            if failed:
                break
            for node_idx in level_list[level]:
                if failed:
                    break
                source_signals = []
                for pre_idx in fanin_list[node_idx]:
                    source_signals.append(y[pre_idx])
                if len(source_signals) > 0:
                    gate_type = x_data[node_idx][1]
                    tmp_y = logic(gate_type, source_signals, gate_to_index)
                    if mask_list[node_idx] == -1:
                        y[node_idx] = tmp_y
                    elif mask_list[node_idx] != tmp_y:
                        failed = True
                        break
                    else:
                        y[node_idx] = tmp_y

        pattern_count = pattern_count + 1
        if not failed:
            success_count += 1
            for idx, x_data_info in enumerate(x_data):
                y1[idx] += y[idx]
    
    if success_count == 0:
        return False, [], []
    for i, _ in enumerate(y1):
        y1[i] = y1[i] / success_count

    return True, y1, 1

def simulator_truth_table(x_data, PI_indexes, level_list, fanin_list, gate_to_index):
    no_of_patterns = int(pow(2, len(PI_indexes)))
    truth_table = []
    for idx in range(len(x_data)):
        truth_table.append([])

    for pattern_idx in range(no_of_patterns):
        input_vector = dec2list(pattern_idx, len(PI_indexes))
        state = [-1] * len(x_data)

        for k, pi_idx in enumerate(PI_indexes):
            state[pi_idx] = input_vector[k]

        for level in range(1, len(level_list), 1):
            for node_idx in level_list[level]:
                source_signals = []
                for pre_idx in fanin_list[node_idx]:
                    source_signals.append(state[pre_idx])
                if len(source_signals) > 0:
                    gate_type = x_data[node_idx][1]
                    res = logic(gate_type, source_signals, gate_to_index)
                    state[node_idx] = res

        for idx in range(len(x_data)):
            truth_table[idx].append(state[idx])
    
    return truth_table


def get_gate_type(line, gate_to_index):
    '''
    Function to get the interger index of the gate type.
    Modified by Min.
    ...
    Parameters:
        line : str, the single line in the bench file.
        gate_to_index: dict, the mapping from the gate name to the integer index
    Return:
        vector_row : int, the integer index for the gate. Currently consider 7 gate types.
    '''
    vector_row = -1
    for (gate_name, index) in gate_to_index.items():
        if gate_name  in line:
            vector_row = index

    if vector_row == -1:
        print(line)
        raise KeyError('[ERROR] Find unsupported gate')

    return vector_row

def add_node_index(data):
    '''
    A pre-processing function to handle with the `.bench` format files.
    Will add the node index before the line, and also calculate the total number of nodes.
    Modified by Min.
    ...
    Parameters:
        data : list(str), the lines read out from a bench file
    Return:
        data : list(str), the updated lines for a circuit
        node_index: int, the number of the circuits, not considering `OUTPUT` lines.
        index_map: dict(int:int), the mapping from the original node name to the updated node index.
    '''
    node_index = 0
    index_map = {}

    for i, val in enumerate(data):
        # node level and index  for PI
        if "INPUT" in val:
            node_name = val.split("(")[1].split(")")[0]
            index_map[node_name] = str(node_index)
            data[i] = str(node_index) + ":" + val[:-1] #+ ";0"
            node_index += 1
            

        # index for gate nodes
        if ("= NAND" in val) or ("= NOR" in val) or ("= AND" in val) or ("= OR" in val) or (
                "= NOT" in val) or ("= XOR" in val):
            node_name = val.split(" = ")[0]
            index_map[node_name] = str(node_index)
            data[i] = str(node_index) + ":" + val[:-1]
            node_index += 1

    return data, node_index, index_map

def new_node(name2idx, x_data, node_name, gate_type):
    x_data.append([node_name, gate_type])
    name2idx[node_name] = len(name2idx)

def feature_gen_connect(data, gate_to_index):
    '''
        A pre-processing function to handle with the modified `.bench` format files.
        Will generate the necessary attributes, adjacency matrix, edge connectivity matrix, etc.
        Modified by Stone 27-09-2021
        Modified by Stone 13-10-2021
            fixed bug: the key word of gates should be 'OR(' instead of 'OR',
            because variable name may be 'MEMORY' has 'OR'
        ...
        Parameters:
            data : list(str), the lines read out from a bench file (after modified by `add_node_index`)
            gate_to_index: dict(str:int), the mapping from the gate name to the gate index.
        Return:
            x_data: list(list((str, int, int))), the node feature matrix with shape [num_nodes, num_node_features], the current dimension of num_node_features is 3, wherein 0th - node_name defined in bench (str); 1st - integer index for the gate type; 2nd - logic level.
            edge_index_data: list(list(int)), the connectivity matrix wiht shape of [num_edges, 2]
            level_list: logic level [max_level + 1, xx]
            fanin_list: the fanin node indexes for each node
            fanout_list: the fanout node indexes for each node
    '''
    name2idx = {}
    node_cnt = 0
    x_data = []
    edge_index_data = []

    for line in data:
        if 'INPUT(' in line:
            node_name = line.split("(")[-1].split(')')[0]
            new_node(name2idx, x_data, node_name, get_gate_type('INPUT', gate_to_index))
        elif 'AND(' in line or 'NAND(' in line or 'OR(' in line or 'NOR(' in line \
                or 'NOT(' in line or 'XOR(' in line or 'BUF(' in line:
            node_name = line.split(':')[-1].split('=')[0].replace(' ', '')
            gate_type = line.split('=')[-1].split('(')[0].replace(' ', '')
            new_node(name2idx, x_data, node_name, get_gate_type(gate_type, gate_to_index))

    for line_idx, line in enumerate(data):
        if 'AND(' in line or 'NAND(' in line or 'OR(' in line or 'NOR(' in line \
                or 'NOT(' in line or 'XOR(' in line or 'BUF(' in line:
            node_name = line.split(':')[-1].split('=')[0].replace(' ', '')
            gate_type = line.split('=')[-1].split('(')[0].replace(' ', '')
            src_list = line.split('(')[-1].split(')')[0].replace(' ', '').split(',')
            dst_idx = name2idx[node_name]
            for src_node in src_list:
                src_node_idx = name2idx[src_node]
                edge_index_data.append([src_node_idx, dst_idx])
    
    return x_data, edge_index_data

def get_level(x_data, fanout_list):
    bfs_q = []
    x_data_level = [-1] * len(x_data)
    max_level = 0
    for idx, x_data_info in enumerate(x_data):
        if x_data_info[1] == 0:
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

def feature_gen_level(x_data, fanout_list, gate_to_index={'GND': 999, 'VDD': 999}):
    bfs_q = []
    x_data_level = [-1] * len(x_data)
    max_level = 0
    for idx, x_data_info in enumerate(x_data):
        if x_data_info[1] == 0 or x_data_info[1] == 'PI':
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
    
    for idx, x_data_info in enumerate(x_data):
        if x_data_info[1] == gate_to_index['GND'] or x_data_info[1] == gate_to_index['VDD']:
            x_data_level[idx] = 0
        elif x_data_info[1] == 'GND' or x_data_info[1] == 'VDD':
            x_data_level[idx] = 0
        else:
            if x_data_level[idx] == -1:
                print('[ERROR] Find unconnected node')
                raise

    if max_level == 0:
        level_list = [[]]
    else:
        for idx in range(len(x_data)):
            level_list[x_data_level[idx]].append(idx)
            x_data[idx].append(x_data_level[idx])
    return x_data, level_list

def get_level_reverse(x_data, fanin_list, fanout_list):
    bfs_q = []
    reverse_level = [-1] * len(x_data)
    max_level = 0
    for idx, x_data_info in enumerate(x_data):
        if len(fanout_list[idx]) == 0 and len(fanin_list[idx]) != 0:
            bfs_q.append(idx)
            reverse_level[idx] = 0
    while len(bfs_q) > 0:
        idx = bfs_q[-1]
        bfs_q.pop()
        tmp_level = reverse_level[idx] + 1
        for next_node in fanin_list[idx]:
            if reverse_level[next_node] < tmp_level:
                reverse_level[next_node] = tmp_level
                bfs_q.insert(0, next_node)
                if reverse_level[next_node] > max_level:
                    max_level = reverse_level[next_node]
    level_list = []
    for level in range(max_level+1):
        level_list.append([])
        
    if max_level == 0:
        level_list = [[]]
    else:
        for idx in range(len(x_data)):
            if reverse_level[idx] >= 0:
                level_list[reverse_level[idx]].append(idx)
    return level_list

def get_fanin_fanout(x_data, edge_index):
    fanout_list = []
    fanin_list = []
    for idx, x_data_info in enumerate(x_data):
        fanout_list.append([])
        fanin_list.append([])
    for edge in edge_index:
        fanout_list[edge[0]].append(edge[1])
        fanin_list[edge[1]].append(edge[0])
    return fanin_list, fanout_list

def get_edge(x_data, fanout_list):
    edge = []
    for idx in range(len(x_data)):
        for fanout_idx in fanout_list[idx]:
            edge.append([idx, fanout_idx])
    return edge

def rename_node(x_data):
    '''
    Convert the data[0] (node name : str) to the index (node index: int)
    ---
    Parameters:
        x_data: list(list(xx)), the node feature matrix
    Return:
        x_data: list(list(xx)), the node feature matrix
    '''
    for idx, x_data_info in enumerate(x_data):
        x_data_info[0] = idx
    return x_data

def rename_node_N(x_data):
    for idx, x_data_info in enumerate(x_data):
        x_data_info[0] = 'N{:}'.format(idx)
    return x_data

def save_bench(file, x_data, fanin_list, fanout_list, gate_to_idx):
    PI_list = []
    PO_list = []
    for idx, ele in enumerate(fanin_list):
        if len(fanin_list[idx]) == 0:
            PI_list.append(idx)
    for idx, ele in enumerate(fanout_list):
        if len(fanout_list[idx]) == 0:
            PO_list.append(idx)
    
    f = open(file, 'w')
    f.write('# {:} inputs\n'.format(len(PI_list)))
    f.write('# {:} outputs\n'.format(len(PO_list)))
    f.write('\n')
    # Input
    for idx in PI_list:
        f.write('INPUT({})\n'.format(x_data[idx][0]))
    f.write('\n')
    # Output
    for idx in PO_list:
        f.write('OUTPUT({})\n'.format(x_data[idx][0]))
    f.write('\n')
    # Gates
    for idx, x_data_info in enumerate(x_data):
        if idx not in PI_list:
            gate_type = None
            for ele in gate_to_idx.keys():
                if gate_to_idx[ele] == x_data_info[1]:
                    gate_type = ele
                    break
            line = '{} = {}('.format(x_data_info[0], gate_type)
            for k, fanin_idx in enumerate(fanin_list[idx]):
                if k == len(fanin_list[idx]) - 1:
                    line += '{})\n'.format(x_data[fanin_idx][0])
                else:
                    line += '{}, '.format(x_data[fanin_idx][0])
            f.write(line)
    f.write('\n')
    f.close()

def justify_po(x_data, fanin_list, reverse_level_list, po_idx, gate_to_index): 
    val = [-1] * len(x_data)    # 0: L0, 1: L1, 2: X, 3: -X
    val[po_idx] = 1
    
    for level in range(len(reverse_level_list)):
        for idx in reverse_level_list[level]:
            fanin_val = reverse_logic(x_data[idx][1], val[idx], gate_to_index)
            for fanin_idx in fanin_list[idx]:
                val[fanin_idx] = fanin_val
    
    return val

def get_picone_list(x_data, fanin_list, level_list):
    picone_list = []
    for idx in range(len(x_data)):
        picone_list.append([])
    for level in range(len(level_list)):
        for idx in level_list[level]:
            if x_data[idx][1] == 0:
                picone_list[idx] = [idx]
            else:
                for fanin_idx in fanin_list[idx]:
                    picone_list[idx] += picone_list[fanin_idx]
                picone_list[idx] = list(set(picone_list[idx]))
                picone_list[idx].sort()
    return picone_list

def parse_bench(file, gate_to_index={'PI': 0, 'AND': 1, 'NOT': 2}):
    data = read_file(file)
    data, num_nodes, _ = add_node_index(data)
    data, edge_data = feature_gen_connect(data, gate_to_index)
    fanin_list, fanout_list = get_fanin_fanout(data, edge_data)
    data, level_list = feature_gen_level(data, fanout_list)
    return data, edge_data, fanin_list, fanout_list, level_list

def parse_graph(x_data, edge_data):
    fanin_list, fanout_list = get_fanin_fanout(x_data, edge_data)
    x_data, level_list = feature_gen_level(x_data, fanout_list)
    return x_data, edge_data, fanin_list, fanout_list, level_list

def identify_reconvergence(x_data, level_list, fanin_list, fanout_list):
    '''
    Function to identify the reconvergence nodes in the given circuit.
    The algorithm is done under the principle that we only consider the minimum reconvergence structure.
    Modified by Stone 27-09-2021
    ...
    Parameters:
        x_data : list(list((str, int, int))), the node feature matrix with shape [num_nodes, num_node_features], the current dimension of num_node_features is 3, wherein 0th - node_name defined in bench (str); 1st - integer index for the gate type; 2nd - logic level; 3rd - C1, 4th - C0, 5th - Obs.
        level_list: logic levels
        fanin_list: the fanin node indexes for each node
        fanout_list: the fanout node indexes for each node
    Return:
        x_data : list(list((str, int, int))), the node feature matrix with shape [num_nodes, num_node_features], the current dimension of num_node_features is 3, wherein 0th - node_name defined in bench (str); 1st - integer index for the gate type; 2nd - logic level; 3rd - C1; 4th - C0; 5th - Obs; 6th - fan-out, 7th - boolean recovengence, 8th - index of the source node (-1 for non recovengence).
        rc_lst: list(int), the index for the reconvergence nodes
    '''
    
    FOL = []
    fanout_num = []
    is_del = []
    # RC (same as reconvergence_nodes)
    rc_lst = []
    max_level = 0
    for x_data_info in x_data:
        if x_data_info[2] > max_level:
            max_level = x_data_info[2]
        FOL.append([])
    for idx, x_data_info in enumerate(x_data):
        fanout_num.append(len(fanout_list[idx]))
        is_del.append(False)

    for level in range(max_level + 1):
        if level == 0:
            for idx in level_list[0]:
                x_data[idx].append(0)
                x_data[idx].append(-1)
                if len(fanout_list[idx]) > 1:
                    FOL[idx].append(idx)
        else:
            for idx in level_list[level]:
                FOL_tmp = []
                FOL_del_dup = []
                save_mem_list = []
                for pre_idx in fanin_list[idx]:
                    if is_del[pre_idx]:
                        print('[ERROR] This node FOL has been deleted to save memory')
                        raise
                    FOL_tmp += FOL[pre_idx]
                    fanout_num[pre_idx] -= 1
                    if fanout_num[pre_idx] == 0:
                        save_mem_list.append(pre_idx)
                for save_mem_idx in save_mem_list:
                    FOL[save_mem_idx].clear()
                    is_del[save_mem_idx] = True
                FOL_cnt_dist = Counter(FOL_tmp)
                source_node_idx = 0
                source_node_level = -1
                is_rc = False
                for dist_idx in FOL_cnt_dist:
                    FOL_del_dup.append(dist_idx)
                    if FOL_cnt_dist[dist_idx] > 1:
                        is_rc = True
                        if x_data[dist_idx][2] > source_node_level:
                            source_node_level = x_data[dist_idx][2]
                            source_node_idx = dist_idx
                if is_rc:
                    x_data[idx].append(1)
                    x_data[idx].append(source_node_idx)
                    rc_lst.append(idx)
                else:
                    x_data[idx].append(0)
                    x_data[idx].append(-1)

                FOL[idx] = FOL_del_dup
                if len(fanout_list[idx]) > 1:
                    FOL[idx].append(idx)
    del (FOL)

    # for node in range(len(x_data)):
    #     x_data[node].append(0)
    # for rc_idx in rc_lst:
    #     x_data[rc_idx][-1] = 1

    return x_data, rc_lst

def new_node_in_aig(x_data, gate_type_num, fanin_list, fanout_list):
    idx = len(x_data)
    x_data.append(['N{:}'.format(len(x_data)), gate_type_num])
    fanin_list.append([])
    fanout_list.append([])
    return idx

def add_edge(src, dst, fanin_list, fanout_list):
    fanin_list[dst].append(src)
    fanout_list[src].append(dst)

def reconnect(IN_PORT_1, IN_PORT_2, OUT_PORT, fanin_list, fanout_list):
    A = fanin_list[OUT_PORT][0]
    B = fanin_list[OUT_PORT][1]
    # INPUT Port
    for k, fanout_idx in enumerate(fanout_list[A]):
        if fanout_idx == OUT_PORT:
            fanout_list[A][k] = IN_PORT_1
    fanin_list[IN_PORT_1].append(A)
    for k, fanout_idx in enumerate(fanout_list[B]):
        if fanout_idx == OUT_PORT:
            fanout_list[B][k] = IN_PORT_2
    fanin_list[IN_PORT_2].append(B)

def convert_two_fanin(x_data, fanin_list, fanout_list, gate_to_index):
    before_len = len(x_data)
    for idx in range(before_len):
        x_data_info = x_data[idx]
        if len(fanin_list[idx]) <= 2:
            continue
        # Clean 
        for pre_idx in fanin_list[idx]:
            while idx in fanout_list[pre_idx]:
                fanout_list[pre_idx].remove(idx)
        tmp_fanin = copy.deepcopy(fanin_list[idx])
        fanin_list[idx] = []
        # Gate - AND / OR
        if x_data_info[1] == gate_to_index['OR'] or x_data_info[1] == gate_to_index['AND']:
            x_a = tmp_fanin[0]
            new_gate_list = []
            for k in range(len(tmp_fanin)):
                if k == 0: continue
                if k == len(tmp_fanin) - 1: continue
                x_b = tmp_fanin[k]
                new_gate_list.append(new_node_in_aig(x_data, x_data_info[1], fanin_list, fanout_list))
                add_edge(x_a, new_gate_list[-1], fanin_list, fanout_list)
                add_edge(x_b, new_gate_list[-1], fanin_list, fanout_list)
                x_a = new_gate_list[-1]
            add_edge(new_gate_list[-1], idx, fanin_list, fanout_list)
            add_edge(tmp_fanin[-1], idx, fanin_list, fanout_list)
        # Gate - NAND / NOR 
        elif x_data_info[1] == gate_to_index['NOR'] or x_data_info[1] == gate_to_index['NAND']:
            x_a = tmp_fanin[0]
            new_gate_list = []
            for k in range(len(tmp_fanin)):
                if k == 0: continue
                x_b = tmp_fanin[k]
                if x_data_info[1] == gate_to_index['NOR']:
                    new_gate_list.append(new_node_in_aig(x_data, gate_to_index['OR'], fanin_list, fanout_list))
                else:
                    new_gate_list.append(new_node_in_aig(x_data, gate_to_index['AND'], fanin_list, fanout_list))
                add_edge(x_a, new_gate_list[-1], fanin_list, fanout_list)
                add_edge(x_b, new_gate_list[-1], fanin_list, fanout_list)
                x_a = new_gate_list[-1]
            add_edge(new_gate_list[-1], idx, fanin_list, fanout_list)
            x_data[idx][1] = gate_to_index['NOT']
        # Gate - XOR
        elif x_data_info[1] == gate_to_index['XOR']:
            raise('XOR has more than 2 fanin')
        # Gate - NOT
        elif x_data_info[1] == gate_to_index['NOT']:
            raise('NOT has more than 1 fanin')
    return x_data, fanin_list, fanout_list

def convert_aig(x_data, fanin_list, fanout_list, gate_to_index):
    for idx, x_data_info in enumerate(x_data):
        if x_data_info[1] == gate_to_index['OR']:
            inv_1_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            inv_2_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            and_1_idx = new_node_in_aig(x_data, gate_to_index['AND'], fanin_list, fanout_list)
            x_data[idx][1] = gate_to_index['NOT']
            # Internal connection 
            add_edge(inv_1_idx, and_1_idx, fanin_list, fanout_list)
            add_edge(inv_2_idx, and_1_idx, fanin_list, fanout_list)
            # External connection
            reconnect(inv_1_idx, inv_2_idx, idx, fanin_list, fanout_list)
            # Final connection 
            fanin_list[idx] = [and_1_idx]
            fanout_list[and_1_idx] = [idx]
        elif x_data_info[1] == gate_to_index['NOR']:
            inv_1_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            inv_2_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            x_data[idx][1] = gate_to_index['AND']
            # External connection 
            reconnect(inv_1_idx, inv_2_idx, idx, fanin_list, fanout_list)
            # Final connection
            fanin_list[idx] = [inv_1_idx, inv_2_idx]
            fanout_list[inv_1_idx] = [idx]
            fanout_list[inv_2_idx] = [idx]
        elif x_data_info[1] == gate_to_index['NAND']:
            and_1_idx = new_node_in_aig(x_data, gate_to_index['AND'], fanin_list, fanout_list)
            x_data[idx][1] = gate_to_index['NOT']
            # External connection 
            reconnect(and_1_idx, and_1_idx, idx, fanin_list, fanout_list)
            # Final connection
            fanin_list[idx] = [and_1_idx]
            fanout_list[and_1_idx] = [idx]
        elif x_data_info[1] == gate_to_index['XOR']:
            inv_3_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            inv_4_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            inv_6_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            inv_8_idx = new_node_in_aig(x_data, gate_to_index['NOT'], fanin_list, fanout_list)
            and_5_idx = new_node_in_aig(x_data, gate_to_index['AND'], fanin_list, fanout_list)
            and_7_idx = new_node_in_aig(x_data, gate_to_index['AND'], fanin_list, fanout_list)
            x_data[idx][1] = gate_to_index['AND']
            # Internal connection 
            add_edge(inv_3_idx, and_5_idx, fanin_list, fanout_list)
            add_edge(inv_4_idx, and_5_idx, fanin_list, fanout_list)
            add_edge(and_5_idx, inv_6_idx, fanin_list, fanout_list)
            add_edge(and_7_idx, inv_8_idx, fanin_list, fanout_list)
            # External connection 
            A = fanin_list[idx][0]
            B = fanin_list[idx][1]
            for k, fanout_idx in enumerate(fanout_list[A]):
                if fanout_idx == idx:
                    fanout_list[A][k] = inv_3_idx
                    fanout_list[A].append(and_7_idx)
                    break
            fanin_list[inv_3_idx].append(A)
            fanin_list[and_7_idx].append(A)
            for k, fanout_idx in enumerate(fanout_list[B]):
                if fanout_idx == idx:
                    fanout_list[B][k] = inv_4_idx
                    fanout_list[B].append(and_7_idx)
                    break
            fanin_list[inv_4_idx].append(B)
            fanin_list[and_7_idx].append(B)
            # Final connection 
            fanin_list[idx] = [inv_6_idx, inv_8_idx]
            fanout_list[inv_6_idx] = [idx]
            fanout_list[inv_8_idx] = [idx]
    return x_data, fanin_list, fanout_list
