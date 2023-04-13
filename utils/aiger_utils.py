import os 
import numpy as np 
import subprocess 

def cnf_to_xdata(cnf_filename, tmp_aig_filename, tmp_aag_filename, gate_to_index):
    cnf2aig_cmd = 'cnf2aig {} {}'.format(cnf_filename, tmp_aig_filename)
    info = os.popen(cnf2aig_cmd).readlines()
    aig2aag_cmd = 'aigtoaig {} {}'.format(tmp_aig_filename, tmp_aag_filename)
    info = os.popen(aig2aag_cmd).readlines()
    
    # read aag
    f = open(tmp_aag_filename, 'r')
    lines = f.readlines()
    f.close()
    header = lines[0].strip().split(" ")
    assert header[0] == 'aag', 'The header of AIG file is wrong.'
    # “M”, “I”, “L”, “O”, “A” separated by spaces.
    n_variables = eval(header[1])
    n_inputs = eval(header[2])
    n_outputs = eval(header[4])
    n_and = eval(header[5])
    if n_outputs != 1 or n_variables != (n_inputs + n_and) or n_variables == n_inputs:
        return None
    assert n_outputs == 1, 'The AIG has multiple outputs.'
    assert n_variables == (n_inputs + n_and), 'There are unused AND gates.'
    assert n_variables != n_inputs, '# variable equals to # inputs'
    # Construct AIG graph
    x_data = []
    edge_index = []
    # node_labels = []
    not_dict = {}
    
    # Add Literal node
    for i in range(n_inputs):
        x_data.append([len(x_data), gate_to_index['PI']])
        # node_labels += [0]

    # Add AND node
    for i in range(n_inputs+1, n_inputs+1+n_and):
        x_data.append([len(x_data), gate_to_index['AND']])
        # node_labels += [1]


    # sanity-check
    for (i, line) in enumerate(lines[1:1+n_inputs]):
        literal = line.strip().split(" ")
        assert len(literal) == 1, 'The literal of input should be single.'
        assert int(literal[0]) == 2 * (i + 1), 'The value of a input literal should be the index of variables mutiplying by two.'

    literal = lines[1+n_inputs].strip().split(" ")[0]
    assert int(literal) == (n_variables * 2) or int(literal) == (n_variables * 2) + 1, 'The value of the output literal shoud be (n_variables * 2)'
    sign_final = int(literal) % 2
    index_final_and = int(literal) // 2 - 1

    for (i, line) in enumerate(lines[2+n_inputs: 2+n_inputs+n_and]):
        literals = line.strip().split(" ")
        assert len(literals) == 3, 'invalidate the definition of two-input AND gate.'
        assert int(literals[0]) == 2 * (i + 1 + n_inputs)
    var_def = lines[2+n_variables].strip().split(" ")[0]

    assert var_def == 'i0', 'The definition of variables is wrong.'
    # finish sanity-check

    # Add edge
    for (i, line) in enumerate(lines[2+n_inputs: 2+n_inputs+n_and]):
        line = line.strip().split(" ")
        # assert len(line) == 3, 'The length of AND lines should be 3.'
        output_idx = int(line[0]) // 2 - 1
        # assert (int(line[0]) % 2) == 0, 'There is inverter sign in output literal.'

        # 1. First edge
        input1_idx = int(line[1]) // 2 - 1
        sign1_idx = int(line[1]) % 2
        # If there's a NOT node
        if sign1_idx == 1:
            if input1_idx in not_dict.keys():
                not_idx = not_dict[input1_idx]
            else:
                x_data.append([len(x_data), gate_to_index['NOT']])
                # node_labels += [2]
                not_idx = len(x_data) - 1
                not_dict[input1_idx] = not_idx
                edge_index += [[input1_idx, not_idx]]
            edge_index += [[not_idx, output_idx]]
        else:
            edge_index += [[input1_idx, output_idx]]


        # 2. Second edge
        input2_idx = int(line[2]) // 2 - 1
        sign2_idx = int(line[2]) % 2
        # If there's a NOT node
        if sign2_idx == 1:
            if input2_idx in not_dict.keys():
                not_idx = not_dict[input2_idx]
            else:
                x_data.append([len(x_data), gate_to_index['NOT']])
                # node_labels += [2]
                not_idx = len(x_data) - 1
                not_dict[input2_idx] = not_idx
                edge_index += [[input2_idx, not_idx]]
            edge_index += [[not_idx, output_idx]]
        else:
            edge_index += [[input2_idx, output_idx]]
    
    
    if sign_final == 1:
        x_data.append([len(x_data), gate_to_index['NOT']])
        # node_labels += [2]
        not_idx = len(x_data) - 1
        edge_index += [[index_final_and, not_idx]]
    
    return x_data, edge_index

def aig_to_xdata(aig_filename, tmp_aag_filename, gate_to_index):
    aig2aag_cmd = 'aigtoaig {} {}'.format(aig_filename, tmp_aag_filename)
    info = os.popen(aig2aag_cmd).readlines()
    
    # read aag
    f = open(tmp_aag_filename, 'r')
    lines = f.readlines()
    f.close()
    header = lines[0].strip().split(" ")
    assert header[0] == 'aag', 'The header of AIG file is wrong.'
    # “M”, “I”, “L”, “O”, “A” separated by spaces.
    n_variables = eval(header[1])
    n_inputs = eval(header[2])
    n_outputs = eval(header[4])
    n_and = eval(header[5])
    # Construct AIG graph
    x_data = []
    edge_index = []
    # node_labels = []
    aigidx_to_nodeidx = {}    
    
    # Add Literal node
    for i in range(n_inputs):
        aigidx_to_nodeidx[(i+1)*2] = len(x_data)
        x_data.append([len(x_data), gate_to_index['PI']])

    # Add AND node
    for i in range(n_and):
        aigidx_to_nodeidx[(i+1+n_inputs)*2] = len(x_data)
        x_data.append([len(x_data), gate_to_index['AND']])

    # Add NOT node 
    for (i, line) in enumerate(lines[1+n_inputs+n_outputs: 1+n_inputs+n_outputs+n_and]):
        arr = line.replace('\n', '').split(' ')
        for ele in arr:
            aigidx = int(ele)
            if aigidx % 2 == 1 and aigidx not in aigidx_to_nodeidx.keys():
                aigidx_to_nodeidx[aigidx] = len(x_data)
                x_data.append([len(x_data), gate_to_index['NOT']])
                edge_index.append([aigidx_to_nodeidx[aigidx-1], aigidx_to_nodeidx[aigidx]])
    
    # Add connection
    for (i, line) in enumerate(lines[1+n_inputs+n_outputs: 1+n_inputs+n_outputs+n_and]):
        arr = line.replace('\n', '').split(' ')
        fanout = int(arr[0])
        fanin_A = int(arr[1])
        fanin_B = int(arr[2])
        edge_index.append([aigidx_to_nodeidx[fanin_A], aigidx_to_nodeidx[fanout]])
        edge_index.append([aigidx_to_nodeidx[fanin_B], aigidx_to_nodeidx[fanout]])
    
    return x_data, edge_index

def aig_to_cnf(data, fanin_list, gate_to_index, const_0=[], const_1=[], add_clauses=[]):
    cnf = []
    for idx, x_data_info in enumerate(data): 
        if x_data_info[1] == gate_to_index['INPUT']:
            continue
        elif x_data_info[1] == gate_to_index['NOT']:
            var_C = idx + 1
            var_A = fanin_list[idx][0] + 1
            cnf.append([-1 * var_C, -1 * var_A])
            cnf.append([var_C, var_A])
        elif x_data_info[1] == gate_to_index['AND']:
            var_C = idx + 1
            var_A = fanin_list[idx][0] + 1
            var_B = fanin_list[idx][1] + 1
            cnf.append([var_C, -1*var_A, -1*var_B])
            cnf.append([-1*var_C, var_A])
            cnf.append([-1*var_C, var_B])
    # Const
    # cnf.append([po_idx + 1])
    for const_0_idx in const_0:
        var = const_0_idx + 1
        cnf.append([-1 * var])
    for const_1_idx in const_1:
        var = const_1_idx + 1
        cnf.append([var])

    # Additional clauses 
    cnf = cnf + add_clauses
    return cnf

def aigcone_to_cnf(data, fanin_list, cone_po, gate_to_index):
    # Mask
    mask = [0] * len(data)
    bfs_q = [cone_po]
    while len(bfs_q) > 0:
        idx = bfs_q[-1]
        mask[idx] = 1
        bfs_q.pop()
        for fanin_idx in fanin_list[idx]:
            if mask[fanin_idx] == 0:
                bfs_q.insert(0, fanin_idx)
    
    # Build CNF
    cnf = []
    for idx, x_data_info in enumerate(data): 
        if mask[idx] == 0:
            continue
        if x_data_info[1] == gate_to_index['INPUT']:
            continue
        elif x_data_info[1] == gate_to_index['NOT']:
            var_C = idx + 1
            var_A = fanin_list[idx][0] + 1
            cnf.append([-1 * var_C, -1 * var_A])
            cnf.append([var_C, var_A])
        elif x_data_info[1] == gate_to_index['AND']:
            var_C = idx + 1
            var_A = fanin_list[idx][0] + 1
            var_B = fanin_list[idx][1] + 1
            cnf.append([var_C, -1*var_A, -1*var_B])
            cnf.append([-1*var_C, var_A])
            cnf.append([-1*var_C, var_B])

    return cnf, np.sum(mask)
