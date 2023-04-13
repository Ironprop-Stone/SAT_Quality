# src_folder = './debug/'
src_folder = '/Users/zhengyuanshi/studio/dataset/LEC/all_case_bench'
emb_folder = '../../../emb/'
gate_to_index={'INPUT': 0, 'AND': 1, 'NOT': 2}

cadical = './cadical/build/cadical'
kissat = './kissat/build/kissat'
solver = kissat 

INIT_SIM_TIMES = 32
MAX_RUNTIME = 100
MAX_PROB_GAP = 0.01

SHUFFLE_TIMES = 2
NUM_COLORS = 6000

REVERSED_ORDER = True

NAME_LIST = [
    # 'ab34'
    # 'b29'
    # 'ab34', 'h25', 'ab7', 'e12'
    # 'h25', 'ab7', 'b29'

    # Debug - small < 3s
    # 'ab34', 
    # Debug - middle 10s~100s
    # 'e12'
    # SAT
    # 'a26', 'b27', 
    # 'b29'
    # # Test - Large
    # 'ad41', 'h25', 'ab1', 'f13', 'ab10', 
    # 'mult_op_DEMO1_13_13_TOP12', 'aa11', 'ad22', 
    # 'ac12', 'f28', 'mult_op_DEMO1_12_12_TOP18', 
    # 'mult_op_DEMO1_10_10_TOP11', 'ac34', 'aa31', 
    # 'mult_op_DEMO1_13_13_TOP20'
    # Test - Middle
    # 'f8', 'ab7', 'b29', 'e1', 'h23', 'b20', 
    # 'ab29', 'ad4', 'mult_op_DEMO1_10_10_TOP16', 'aa11', 
    # 'f28'
]