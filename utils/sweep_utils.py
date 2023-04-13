import utils.cnf_utils as cnf_utils
import torch

def get_hash(plaintext):
    res = 0
    for ele in plaintext:
        res += (int(ele) * 291143 + 2908361) 
        res %= int(1e7+1)
    return res

def verify_equ(cnf_node_a, cnf_node_b, node_a, node_b, no_vars, PI_list):
    solve_cnf = cnf_node_a + cnf_node_b
    # Miter XOR
    var_po = no_vars + 1
    var_a = node_a + 1
    var_b = node_b + 1
    # solve_cnf.append([-1*var_a, -1*var_b, -1*var_po])
    # solve_cnf.append([ 1*var_a,  1*var_b, -1*var_po])
    # solve_cnf.append([ 1*var_a, -1*var_b,  1*var_po])
    # solve_cnf.append([-1*var_a,  1*var_b,  1*var_po])
    # solve_cnf.append([1*var_po])
    solve_cnf.append([-1*var_a, -1*var_b])
    solve_cnf.append([var_a, var_b])

    is_sat, asg, tot_time = cnf_utils.kissat_solve(solve_cnf, no_vars+1)
    
    sol = []
    if is_sat:
        for pi_idx in PI_list:
            sol.append(asg[pi_idx])

    return is_sat, sol

def update_func(func, y):
    for idx in range(len(func)):
        func[idx] = get_hash([func[idx], y[idx]])
    return func

def get_groups(func):
    groups = {}
    for idx in range(len(func)):
        if func[idx] != -1:
            if func[idx] not in groups.keys():
                groups[func[idx]] = [idx]
            else:
                groups[func[idx]].append(idx)
    return groups

def is_equgroup_exist(groups, verified_equ_pairs):
    for key in groups.keys():
        if len(groups[key]) > 1:
            for i in range(0, len(groups[key])):
                for j in range(i+1, len(groups[key])):
                    node_A = groups[key][i]
                    node_B = groups[key][j]
                    if (node_A, node_B) not in verified_equ_pairs:
                        return True, (node_A, node_B)
    return False, (-1, -1)

def read_emb(emb_filename):
    emb = torch.load(emb_filename, map_location=torch.device('cpu'))
    return emb
