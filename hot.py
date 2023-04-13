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

options = {
    'node_color': 'black',
    'node_size': 100,
    'width': 3,
}

if __name__ == '__main__':
    logger = Logger('baseline.log')
    if len(NAME_LIST) == 0:
        for ckt_filename in glob.glob(os.path.join(src_folder, '*.bench')):
            circuit_name = ckt_filename.split('/')[-1].split('.')[0]
            NAME_LIST.append(circuit_name)

    for circuit_name in NAME_LIST:
        ckt_filename = os.path.join(src_folder, '{}.bench'.format(circuit_name))
        if not os.path.exists(ckt_filename):
            continue
        tot_time = []

        # Parse circuit
        logger.write('[BASE-INFO] {} Read ... {}'.format(datetime.now(), circuit_name))
        x_data, edge_data, fanin_list, fanout_list, level_list = circuit_utils.parse_bench(ckt_filename, gate_to_index)
        assert len(level_list[-1]) == 1
        po_idx = level_list[-1][0]

        # Save CNF
        cnf = aiger_utils.aig_to_cnf(x_data, fanin_list, gate_to_index, [], [po_idx])

        # Augment (Shuffle) CNF
        for shuffle_times in range(SHUFFLE_TIMES):
            new_cnf, old2new, new2old = cnf_utils.shuffle_cnf(cnf, len(x_data))
            is_sat, asg, learnt, runtime = cnf_utils.solve_with_learnt(solver, new_cnf, len(x_data))
            learnt = cnf_utils.transfer_cnf_index(learnt, new2old)

            # # with learnt clauses 
            # new_is_sat, _, _, new_runtime = cnf_utils.solve_with_learnt(solver, cnf+learnt, len(x_data))
            # print("Runtime: {:.2f} , {:.2f}".format(runtime, new_runtime))
            # print("Result: {}, {}".format(is_sat, new_is_sat))
            # print()
            # exit(0)

            # Print
            logger.write('Circuit Name: {}, Size: {}, Learnt: {}'.format(circuit_name, len(x_data), len(learnt)))
            logger.write("Result: {}, Runtime: {:.2f} s".format(is_sat, runtime))
            logger.write()

            # Statistics hot
            learnt_times = [0] * len(x_data)
            for learnt_clause in learnt:
                for var in learnt_clause:
                    learnt_times[abs(var) - 1] += 1
            times_dict = {}
            for idx in range(len(x_data)):
                times = learnt_times[idx]
                if times not in times_dict:
                    times_dict[times] = [idx]
                else:
                    times_dict[times].append(idx)

            # Networkx
            G = nx.DiGraph()
            color_map = [''] * len(x_data)
            for idx, x_data_info in enumerate(x_data):
                G.add_node(idx)
                color_map[idx] = 'cornsilk'
            for src, x_data_info in enumerate(x_data):
                for dst in fanout_list[src]:
                    G.add_edge(src, dst)

            keys = list(times_dict.keys())
            keys.sort()
            colors = plt.get_cmap('Reds', len(keys))
            for key in keys:
                # print(len(keys), key, colors(key))
                for idx in times_dict[key]:
                    color_map[idx] = colors(key)

            # Layout and Display 
            for idx in range(len(x_data)):
                G.nodes[idx]["level"] = x_data[idx][2]
            pos = nx.multipartite_layout(G, subset_key="level")

            plt.figure(figsize=(80, 40))
            nx.draw_networkx(G, pos=pos, node_size=100, font_size=5, 
                            node_color=color_map, with_labels=True)
            pdf_filename = './fig/{}_{:}.pdf'.format(circuit_name, shuffle_times)
            plt.savefig(pdf_filename)
            plt.close()
