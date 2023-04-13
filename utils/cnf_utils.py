import enum
import os
import utils.utils as utils
import random
import numpy as np
import time
import copy
from datetime import datetime

def kissat_solve_cnf(cnf_filename):
    cmd_solve = '{} -q {}'.format('kissat', cnf_filename)
    solve_info, solvetime = utils.run_command(cmd_solve)
    is_sat = True
    for line in solve_info:
        if 'UNSATISFIABLE' in line:
            is_sat = False
            break
    return is_sat, solvetime

def save_cnf(iclauses, n_vars, filename): 
    n_clauses = len(iclauses)
    f = open(filename, 'w')
    # head
    f.write('p cnf {:} {:}\n'.format(n_vars, n_clauses))

    # CNF
    for clause in iclauses:
        new_line = ''
        for ele in clause:
            new_line += str(ele) + ' '
        new_line += '0\n'
        f.write(new_line)
    
    f.close()
    
def save_bench(iclauses, n_vars, filename):
    f = open(filename, 'w')
    for pi_idx in range(1, n_vars + 1):
        f.write('INPUT({:})\n'.format(pi_idx))
    f.write('OUTPUT(PO)\n')
    f.write('\n')
    for pi_idx in range(1, n_vars + 1):
        f.write('{:}_INV = NOT({:})\n'.format(pi_idx, pi_idx))
    for clause_idx, clause in enumerate(iclauses):
        newline = 'CLAUSE_{:} = OR('.format(clause_idx)
        for var_idx, var in enumerate(clause):
            if var > 0:
                newline += '{:}'.format(var)
            else:
                newline += '{:}_INV'.format(abs(var))
            if var_idx == len(clause) - 1:
                newline += ')\n'
            else:
                newline += ', '
        f.write(newline)
    newline = 'PO = AND('
    for clause_idx in range(len(iclauses)):
        if clause_idx == len(iclauses) - 1:
            newline += 'CLAUSE_{:})\n'.format(clause_idx)
        else:
            newline += 'CLAUSE_{:}, '.format(clause_idx)
    f.write(newline)
    f.close()
        
def solve(iclauses, no_vars): 
    start_time = time.time()
    if len(iclauses) == 0:
        return False
    solver = minisolvers.MinisatSolver()
    
    for var_idx in range(no_vars):
        solver.new_var(dvar=True)
    for clause in iclauses:
        solver.add_clause(clause)
        
    sat = solver.solve()
    asg = []
    if sat:
        asg = solver.get_model()
    end_time = time.time()
    tot_time = end_time - start_time
    return sat, asg, tot_time

def parse_solution(solve_info, no_vars):
    asg = [0] * no_vars
    for idx, line in enumerate(solve_info):
        if 'Learnt' in line:
            continue
        if line[0] == 's':
            continue
        arr = line.replace('v ', '').replace('\n', '').split(' ')
        for ele in arr:
            num = int(ele)
            if num == 0:
                break
            elif num > 0:
                asg[num - 1] = 1
            else:
                asg[abs(num) - 1] = 0
    return asg

def cadical_solve(iclauses, no_vars, tmp_filename=None, mode=None, args=""):
    if tmp_filename == None:
        tmp_filename = './tmp/tmp_solve_{:}_{:}_{:}_{:}.cnf'.format(datetime.now().hour, datetime.now().minute, len(iclauses), random.randint(0, 100))
    save_cnf(iclauses, no_vars, tmp_filename)
    if mode != None:
        cmd_solve = '{} --{} {} -q {}'.format('cadical', mode, args, tmp_filename)
    else:
        cmd_solve = '{} {} -q {}'.format('cadical', args, tmp_filename)
        
    solve_info, solvetime = utils.run_command(cmd_solve)
    is_sat = True
    for line in solve_info:
        if 'UNSATISFIABLE' in line:
            is_sat = False
            break
    os.remove(tmp_filename)

    if is_sat:
        asg = parse_solution(solve_info, no_vars)
    else:
        asg = []
    return is_sat, asg, solvetime

def kissat_solve(iclauses, no_vars, tmp_filename=None, mode=None):
    if tmp_filename == None:
        tmp_filename = './tmp/tmp_solve_{:}_{:}_{:}_{:}.cnf'.format(
            datetime.now().hour, datetime.now().minute, datetime.now().second, random.randint(0, 10000)
        )
    save_cnf(iclauses, no_vars, tmp_filename)
    if mode != None:
        cmd_solve = '{} --{} -q {}'.format('kissat', mode, tmp_filename)
    else:
        cmd_solve = '{} -q {}'.format('kissat', tmp_filename)
        
    solve_info, solvetime = utils.run_command(cmd_solve)
    is_sat = True
    for line in solve_info:
        if 'UNSATISFIABLE' in line:
            is_sat = False
            break
    os.remove(tmp_filename)

    if is_sat:
        asg = parse_solution(solve_info, no_vars)
    else:
        asg = []
    return is_sat, asg, solvetime

def learned_clauses_solve(iclauses, no_vars, tmp_filename=None, mode=None):
    cadical = '/uac/gds/zyshi21/studio/cadical/build/cadical'
    if tmp_filename == None:
        tmp_filename = './tmp_cadical_solve.cnf'
    save_cnf(iclauses, no_vars, tmp_filename)
    if mode != None:
        cmd_solve = '{} --{} -q {}'.format(cadical, mode, tmp_filename)
    else:
        cmd_solve = '{} -q {}'.format(cadical, tmp_filename)
        
    solve_info, solvetime = utils.run_command(cmd_solve)
    is_sat = True
    for line in solve_info:
        if 'UNSATISFIABLE' in line:
            is_sat = False
            break
    os.remove(tmp_filename)

    # learned clauses 
    learned_clauses = []
    for line in solve_info:
        if 'learned clause:' in line:
            ele = line.replace('\n', '').split(':')
            clause_size = int(ele[1].replace(':'))
            clause = ele[2].replace(' ', '').split(',')[:clause_size]
            learned_clauses.append(clause)

    return is_sat, solvetime, learned_clauses

def read_cnf(cnf_path):
    f = open(cnf_path, 'r')
    lines = f.readlines()
    f.close()

    n_vars = -1
    n_clauses = -1
    begin_parse_cnf = False
    iclauses = []
    for line in lines:
        if begin_parse_cnf:
            arr = line.replace('\n', '').split(' ')
            clause = []
            for ele in arr:
                if ele.replace('-', '').isdigit() and ele != '0':
                    clause.append(int(ele))
            if len(clause) > 0:
                iclauses.append(clause)
                
        elif line.replace(' ', '')[0] == 'c':
            continue
        elif line.replace(' ', '')[0] == 'p': 
            arr = line.replace('\n', '').split(' ')
            get_cnt = 0
            for ele in arr:
                if ele == 'p':
                    get_cnt += 1
                elif ele == 'cnf':
                    get_cnt += 1
                elif ele != '':
                    if get_cnt == 2:
                        n_vars = int(ele)
                        get_cnt += 1
                    else: 
                        n_clauses = int(ele)
                        break
            assert n_vars != -1
            assert n_clauses != -1
            begin_parse_cnf = True
        
    
    return iclauses, n_vars

def divide_cnf(cnf, no_vars, no_sub_cnfs):
    mark_list = [0] * len(cnf)
    for k in range(no_sub_cnfs - 1):
        mark_list[k] = 1
    random.shuffle(mark_list)
    
    sub_cnf_list = []
    sub_cnf = []
    for clause_idx in range(len(cnf)):
        if mark_list[clause_idx] == 1:
            sub_cnf_list.append(sub_cnf)
            sub_cnf = []
        sub_cnf.append(cnf[clause_idx])
    
    sub_cnf_list.append(sub_cnf)
    return sub_cnf_list

def get_BCPsub_cnf(cnf, var, is_inv):
    res_cnf = []
    if not is_inv:
        for clause in cnf:
            if not var in clause:
                tmp_clause = clause.copy()
                for idx, ele in enumerate(tmp_clause):
                    if ele == -var:
                        del tmp_clause[idx]
                res_cnf.append(tmp_clause)
    else:
        for clause in cnf:
            if not -var in clause:
                tmp_clause = clause.copy()
                for idx, ele in enumerate(tmp_clause):
                    if ele == var:
                        del tmp_clause[idx]
                res_cnf.append(tmp_clause)
    return res_cnf

def partition_cnf(cnf, n_vars, partition_times, sub_cnfs=[]):
    if partition_times == 0:
        sub_cnfs.append(cnf)
        return sub_cnfs
    
    var_times = [0] * (n_vars + 1)
    for clause in cnf:
        for var in clause:
            var_times[abs(var)] += 1

    var_sort = np.argsort(var_times)
    most_var = var_sort[-1]
    if var_times[most_var] == 0:
        sub_cnfs.append(cnf)
        return sub_cnfs
    
    # Expansion 
    for most_var in var_sort[::-1]:
        next_var = False
        # Get sub-CNFs
        exp_T_cnf = get_sub_cnf(cnf, most_var, 0)
        exp_F_cnf = get_sub_cnf(cnf, most_var, 1)
        # Verify the expansion
        for clause in exp_T_cnf:
            if len(clause) == 0:
                next_var = True
                print('Find empty clause when parition {:}'.format(most_var))
                break
        for clause in exp_F_cnf:
            if len(clause) == 0:
                next_var = True
                print('Find empty clause when parition {:}'.format(most_var))
                break
        if not next_var:
            break
    if most_var == 0:
        sub_cnfs.append(cnf)
        return sub_cnfs
    
    # Expansion next level 
    sub_cnfs = partition_cnf(exp_T_cnf, n_vars, partition_times-1, sub_cnfs)
    sub_cnfs = partition_cnf(exp_F_cnf, n_vars, partition_times-1, sub_cnfs)
    
    return sub_cnfs

def partition_solve(cnf, n_vars, partition_times, results=[]):
    if partition_times == 0:
        issat, _ = solve(cnf, n_vars)
        results.append(issat)
        return results
    
    var_times = [0] * (n_vars + 1)
    for clause in cnf:
        for var in clause:
            var_times[abs(var)] += 1
            
    most_var = -1
    most_value = 0
    for var_idx in range(len(var_times)):
        if var_times[var_idx] > most_value:
            most_var = var_idx
            most_value = var_times[var_idx]
    if var_times[most_var] == 0:
        issat, _ = solve(cnf, n_vars)
        results.append(issat)
        return results
    
    # Expansion 
    # Get sub-CNFs
    exp_T_cnf = get_sub_cnf(cnf, most_var, 0)
    has_empty = False
    for clause in exp_T_cnf:
        if len(clause) == 0:
            has_empty = True
            break
    if has_empty:
        results.append(False)
    else:
        results = partition_solve(exp_T_cnf, n_vars, partition_times-1, results)
    
    exp_F_cnf = get_sub_cnf(cnf, most_var, 1)
    has_empty = False
    for clause in exp_F_cnf:
        if len(clause) == 0:
            has_empty = True
            break
    if has_empty:
        results.append(False)
    else:
        results = partition_solve(exp_F_cnf, n_vars, partition_times-1, results)
    
    return results

def solve_with_learnt(solver, iclauses, no_vars, tmp_filename=None, mode=None):
    if tmp_filename == None:
        tmp_filename = './tmp/tmp_solve_{:}_{:}_{:}_{:}.cnf'.format(datetime.now().hour, datetime.now().minute, len(iclauses), random.randint(0, 100))
    save_cnf(iclauses, no_vars, tmp_filename)
    if mode != None:
        cmd_solve = '{} --{} -q {}'.format(solver, mode, tmp_filename)
    else:
        cmd_solve = '{} -q {}'.format(solver, tmp_filename)
        
    solve_info, solvetime = utils.run_command(cmd_solve)

    # Parse learnt clauses 
    learnt_clauses = []
    for line in solve_info:
        if 'Learnt' in line:
            ele = line.replace('\n', '').replace(' ', '').split(':')
            # no_var_in_clause = int(ele[1])
            clause = []
            lits = ele[-1].split(',')
            for lit in lits:
                if lit == '':
                    continue
                clause.append(int(lit))
            learnt_clauses.append(clause)

    # Check satisfibility
    is_sat = True
    is_unknown = True
    for line in solve_info:
        if 'UNSATISFIABLE' in line:
            is_unknown = False
            is_sat = False
            break
        if 'SATISFIABLE' in line:
            is_unknown = False
    os.remove(tmp_filename)

    if is_sat and not is_unknown:
        asg = parse_solution(solve_info, no_vars)
        # asg = ['SAT']
    else:
        asg = []
    # Sat Status: SAT=1, UNSAT=0, UNKNOWN=-1
    if is_unknown:
        sat_status = -1
    elif is_sat:
        sat_status = 1
    else:
        sat_status = 0

    return sat_status, asg, learnt_clauses, solvetime

def gen_check_equ_cnf(cnf, node_a, node_b):
    equ_const = []
    var_a = node_a + 1
    var_b = node_b + 1
    equ_const.append([ 1*var_a, -1*var_b])
    equ_const.append([-1*var_a,  1*var_b])

    return cnf+equ_const, equ_const

def gen_const_cnf(cnf, x_data, node_idx, node_val):
    # Get var from node_index
    const_var = node_idx + 1
    if node_val == 0:
        new_const = [-1*const_var]
    else:
        new_const = [const_var]

    # Generate solving CNF
    new_cnf = []
    for clause in cnf:
        is_succ = True
        for lit in clause:
            lit_idx = abs(lit)-1
            if x_data[lit_idx][2] > x_data[node_idx][2]:
                is_succ = False
                break
        if is_succ:
            new_cnf.append(clause)
    if len(new_cnf) > 0:
        new_cnf.append(new_const)
    return new_cnf, new_const

def transfer_cnf_index(cnf, map):
    new_cnf = []
    for clause in cnf:
        new_clause = []
        for lit in clause:
            new_lit = map[abs(lit)]
            if lit < 0:
                new_lit = -1 * new_lit
            new_clause.append(new_lit)
        new_cnf.append(new_clause)
    return new_cnf

def shuffle_cnf(cnf, no_var):
    old2new = {}
    new2old = {}
    old_index = []
    for idx in range(no_var):
        old_index.append(idx+1)
    random.shuffle(old_index)
    for idx in range(no_var):
        old2new[idx+1] = old_index[idx]
        new2old[old_index[idx]] = idx+1

    new_cnf = transfer_cnf_index(cnf, old2new)
    return new_cnf, old2new, new2old
