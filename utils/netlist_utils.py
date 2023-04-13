import enum
import numpy as np
import os

class Gate:
    def __init__(self, gate_name, gate_type) -> None:
        self.name = gate_name
        self.type = gate_type
        self.fanin_list = []
    def update_fanin(self, fanin_list): 
        self.fanin_list = fanin_list

def read_netlist_line(line):
    fanin_pin_list = []
    line = line.replace(' ', '')
    ele_list = line.replace('(', '*').replace(')', '*').split('*')[::-1]
    fanout_pin = ele_list[2]
    ele_idx = 4
    while ele_idx < len(ele_list):
        ele_name = ele_list[ele_idx]
        if 'Cell_' not in ele_name:
            fanin_pin_list.append(ele_name)
        else:
            break
        ele_idx += 2
        
    return fanin_pin_list, fanout_pin

def get_bench_line(fanin_pin_list, fanout_pin, gate_type):
    line = '{} = {}('.format(fanout_pin, gate_type)
    for k, fanin_pin in enumerate(fanin_pin_list):
        if k == len(fanin_pin_list) - 1:
            line += '{})\n'.format(fanin_pin)
        else:
            line += '{}, '.format(fanin_pin)
    return line
    
def parse_netlist_bench(netlist_filename, bench_filename):
    netlist_file = open(netlist_filename, 'r')
    lines = netlist_file.readlines()
    netlist_file.close()
    
    input_line_start = -1
    output_line_start = -1
    wire_line_start = -1
    gate_line_start = -1
    
    for line_idx, line in enumerate(lines):
        if 'input' in line:
            input_line_start = line_idx
        elif 'output' in line:
            output_line_start = line_idx
        elif 'wire' in line:
            wire_line_start = line_idx
        elif '.A' in line and '.Y' in line:
            gate_line_start = line_idx
            break
    
    # Parse PI and PO 
    input_line = ''
    for line_idx, line in enumerate(lines):
        if line_idx >= input_line_start and line_idx < output_line_start:
            input_line += line.replace('input', '').replace(' ', '').replace('\n', '').replace(';', '')
    PI_list = input_line.split(',')
    output_line = ''
    for line_idx, line in enumerate(lines):
        if line_idx >= output_line_start and line_idx < wire_line_start:
            output_line += line.replace('output', '').replace(' ', '').replace('\n', '').replace(';', '')
    PO_list = output_line.split(',')
    
    # Parse Gate
    allGatesVec = []
    for line_idx, line in enumerate(lines):
        if line_idx < gate_line_start:
            continue
        if 'Cell_AND' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'AND')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_OR' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'OR')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_XOR' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'XOR')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_NAND' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'NAND')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_NOR' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'NOR')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_INV' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'NOT')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
        elif 'Cell_BUF' in line:
            fanin_list, fanout = read_netlist_line(line)
            gate_inst = Gate(fanout, 'BUFF')
            gate_inst.update_fanin(fanin_list)
            allGatesVec.append(gate_inst)
            
    # Write PI and PO
    has_fanout = {}
    for gate in allGatesVec:
        for fanin in gate.fanin_list:
            has_fanout[fanin] = 1
        
    f = open(bench_filename, 'w')
    f.write('# PO Name: {}\n'.format(PO_list[0]))
    f.write('\n')
    for pi_name in PI_list:
        if pi_name in has_fanout.keys():
            f.write('INPUT({})\n'.format(pi_name))
    assert len(PO_list) == 1
    for po_name in PO_list:
        f.write('OUTPUT({})\n'.format(po_name))
    f.write('\n')
    
    # Write Gates
    for gate in allGatesVec:
        f.write(get_bench_line(gate.fanin_list, gate.name, gate.type))
    
    f.write('\n')
    f.close()
    
    return PO_list[0]

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