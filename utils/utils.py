import time
import os
import math
import numpy as np 
import torch
# from communities.algorithms import louvain_method, girvan_newman

def read_emb(emb_filename):
    emb = torch.load(emb_filename, map_location=torch.device('cpu'))
    return emb

def rename_node(x_data):
    for idx in range(len(x_data)):
        x_data[idx][0] = idx
    return x_data

def run_command(cmd):
    start_time = time.time()
    info = os.popen(cmd).readlines()
    end_time = time.time()
    runtime = end_time - start_time
    return info, runtime

def community_CIG(n_var, cnf):
    connect_list = []
    adj_matrix = np.zeros((len(cnf), len(cnf)))
    for var_idx in range(n_var + 1):
        connect_list.append([])
    for clause_idx, clause in enumerate(cnf):
        for var in clause:
            connect_list[int(abs(var))].append(clause_idx)
    
    # Clause Incidence Graph
    for var_idx in range(1, n_var+1, 1):
        var_connect = connect_list[var_idx]
        if len(var_connect) == 0 or len(var_connect) == 1:
            continue
        connect_length = math.factorial(len(var_connect)) / (math.factorial(2) * math.factorial(len(var_connect) - 2))
        for i in range(len(var_connect)):
            for j in range(i+1, len(var_connect), 1):
                adj_matrix[var_connect[i]][var_connect[j]] += 1.0 / connect_length
                adj_matrix[var_connect[j]][var_connect[i]] += 1.0 / connect_length
                
    # Partition 
    com, partition = louvain_method(adj_matrix)
    return com, partition[-1]['Q']

def community(n_var, cnf):
    adj_matrix = np.zeros((n_var, n_var))
    
    # Variable Incidence Graph
    for clause in cnf: 
        if len(clause) == 0 or len(clause) == 1:
            continue
        elif len(clause) == 2:
            connect_length = 1
        else:
            connect_length = math.factorial(len(clause)) / (math.factorial(2) * math.factorial(len(clause) - 1))
        for i in range(len(clause)):
            for j in range(i+1, len(clause), 1):
                var_i = abs(clause[i]) - 1
                var_j = abs(clause[j]) - 1
                adj_matrix[var_i][var_j] += 1.0 / connect_length
                adj_matrix[var_i][var_j] += 1.0 / connect_length
                
    # Partition 
    com, partition = louvain_method(adj_matrix)
    return com, partition[-1]['Q']
