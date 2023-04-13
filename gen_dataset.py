import argparse
import glob
import os
import sys
import platform
import time
import torch
import random
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime

import utils.lut_utils as lut_utils 
import utils.circuit_utils as circuit_utils
import utils.aiger_utils as aiger_utils
import utils.mig_utils as mig_utils
import utils.cnf_utils as cnf_utils
from utils.mig_parallel_simulator import pa_simulator
import utils.utils as utils
from utils.logger import Logger
from parameter import *

MAX_CIRCUIT_SIZE = 10000
MAX_SOLVE_TIME = 100
output_folder = 'npz'

if __name__ == '__main__':
    for ckt_filename in glob.glob(os.path.join(src_folder, '*.bench')):
        circuit_name = ckt_filename.split('/')[-1].split('.')[0]
        NAME_LIST.append(circuit_name)
    graphs = {}
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for ckt_idx, circuit_name in enumerate(NAME_LIST):
        ckt_filename = os.path.join(src_folder, '{}.bench'.format(circuit_name))
        if not os.path.exists(ckt_filename):
            continue
        tot_time = []

        # Parse circuit
        x_data, edge_data, fanin_list, fanout_list, level_list = circuit_utils.parse_bench(ckt_filename, gate_to_index)
        if len(x_data) > MAX_CIRCUIT_SIZE:
            continue
        assert len(level_list[-1]) == 1
        po_idx = level_list[-1][0]

        # Save CNF and Solve
        cnf = aiger_utils.aig_to_cnf(x_data, fanin_list, gate_to_index, [], [po_idx])
        print('='*20)
        print('Circuit Name: {}, [{:} / {:}]'.format(circuit_name, ckt_idx, len(NAME_LIST)))
        print('Size: {}, CNF Size: {}'.format(len(x_data), len(cnf)))
        is_sat, asg, learnt, runtime = cnf_utils.solve_with_learnt(solver, cnf, len(x_data), mode='time={:}'.format(MAX_SOLVE_TIME))
        if is_sat == -1:
            print('Unknown')
            print()
            continue
        else:
            print('SAT' if is_sat else 'UNSAT')
        if len(learnt) == 0:
            print('No learnt clause')
            print()
            continue

        # Statistics hot
        learnt_times = [0] * len(x_data)
        for learnt_clause in learnt:
            for var in learnt_clause:
                learnt_times[abs(var) - 1] += 1
        for idx in range(len(x_data)):
            learnt_times[idx] /= len(learnt)
        
        # Save 
        graphs[circuit_name] = {
            'x': x_data, 
            'edge_index': edge_data, 
            'x_hot': learnt_times
        }
        print()

        
    output_filename = os.path.join(output_folder, 'graphs.npz')
    np.savez_compressed(output_filename, graphs=graphs)
    print(output_filename)
    print(len(graphs))


