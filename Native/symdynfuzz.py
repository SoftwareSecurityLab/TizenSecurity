import angr
import claripy
import nose
import os
import sys
import subprocess
import multiprocessing
import logging
import avatar2
import time
import datetime
import random
import string
import signal
from angr_targets import AvatarGDBConcreteTarget
from termcolor import colored

from ssh_fuzz_status import *
from report import report_export
from CFGPartAnalysis import *

binary_x86 = "test001"
GDB_SERVER_IP = 'IP.IP.IP.IP'
GDB_SERVER_PORT = 2323
SSH_USERNAME = "username"
SSH_PASSWORD = "pass"
PROGRAM_NAME = "test001"
ENTRY_POINT = 0x0
sus_function_stdin = ['__isoc99_scanf', 'fgets', 'gets']
sus_function_argv = ['memcpy', 'strcpy', 'strncpy', 'strcat', 'memmove', 'sprintf']
PROGRAM_STATUS_FUZZING = ""
MAX_FUZZ_SIZE = 100
REPORT_FILENAME = "CRASH_REPORT.txt"
CRASH_COUNTER = 0


def execute_concretly(p, state, address, memory_concretize=[], register_concretize=[], timeout=0):
    simgr = p.factory.simgr(state)
    simgr.use_technique(angr.exploration_techniques.Symbion(find=[address], memory_concretize=memory_concretize,
                                                            register_concretize=register_concretize, timeout=timeout))
    exploration = simgr.run()
    return exploration.stashes['found'][0]

def create_concrete_connection(argvs):
    avatar_gdb = AvatarGDBConcreteTarget(avatar2.archs.x86.X86, GDB_SERVER_IP, GDB_SERVER_PORT)
    p = angr.Project(binary_x86, concrete_target=avatar_gdb, use_sim_procedures=True,
                     page_size=0x1000)
    entry_state = p.factory.entry_state()
    entry_state.options.add(angr.options.SYMBION_SYNC_CLE)
    entry_state.options.add(angr.options.SYMBION_KEEP_STUBS_ON_SYNC)
    return p, entry_state, avatar_gdb

def create_ssh_connection(ip, args, fuzz_input):
    sys.stdin = os.fdopen(0)
    arg = ""
    for i in range(0, len(args)):
        arg += args[i] + " "
    subprocess.run(["./connect_ssh_DESKTOP.sh", ip, arg[:-1], SSH_USERNAME, SSH_PASSWORD], input=bytes((fuzz_input).encode()))
    #ret subproccess for future reuse and interact with program on the target

def getListAddressOfFunctionCall(project, cfg, funcName):
    result = []
    analyz = CFGPartAnalysis(project, cfg)
    for name, addrs in analyz.getAddressOfFunctionCall(funcName,dict_type=True).items():
        for add in addrs:
            result.append(add)
    return result

def getFuncAddress(cfg, funcName, plt=None):
    found = [
        addr for addr,func in cfg.kb.functions.items()
        if funcName == func.name and (plt is None or func.is_plt == plt)
        ]
    if len( found ) > 0:
        print("Found "+funcName+"'s address at "+hex(found[0])+"!")
        return found[0]
    else:
        print("No address found for function : "+funcName)
    
def getReturnAddress(concrete_state):
    ret_address_symbolic = concrete_state.mem[concrete_state.regs.esp].int.resolved
    #ret_address_concrete = ret_address_symbolic._model_concrete.value
    return ret_address_symbolic

def getBufferAddress(concrete_state):
    stdin_buffer_address_symbolic = concrete_state.mem[concrete_state.regs.esp].int.resolved
    #stdin_buffer_address_concrete = stdin_buffer_address_symbolic._model_concrete.value
    return stdin_buffer_address_symbolic

def normalize_solved_string(binary_configuration):
    start = 0
    end = 0
    normalized_result = b''
    for i in range(0, len(binary_configuration)):
        if binary_configuration[i] != 0:
            normalized_result += bytes(chr(binary_configuration[i]).encode())
        else:
            normalized_result += b'X'
    i = len(normalized_result) - 1
    while i >= 0:
        if normalized_result[-1] == ord('X'):
            normalized_result = normalized_result[:-1]
        else:
            break
        i -= 1
    return normalized_result


#generalize the function for stdin and solve stdin buffers
def solve(p, project, funcName, concrete_state, symbolic_buffer_address, arg_sym, cfg,path_number):
    target_address = getListAddressOfFunctionCall(project, cfg, funcName)
    func_addr = getFuncAddress(cfg, funcName, plt=True)
    simgr = p.factory.simgr(concrete_state)
    exploration = simgr.explore(find=target_address[path_number])
    solved_item = []
    solved_args = []
    solution_argvs = []
    if exploration.stashes['found']:
        new_symbolic_state = exploration.stashes['found'][0]
        for i in range(0, len(symbolic_buffer_address)):
            binary_configuration = new_symbolic_state.solver.eval(arg_sym[i], cast_to=bytes)
            '''data = hex(binary_configuration)[2:]
            if len(data) % 2 == 1:
                data += '0'
            byte_configuration = bytes.fromhex(data)
            '''
            binary_configuration = normalize_solved_string(binary_configuration)
            binary_configuration_noNull = binary_configuration.replace(b'\x00', b'')
            solution_argvs.append(binary_configuration_noNull.decode('windows-1252'))
            solved_item.append(symbolic_buffer_address[i])
            solved_item.append(arg_sym[i])
            solved_args.append((solved_item))
            solved_item = []
        return (solved_args, solution_argvs, new_symbolic_state, func_addr)
    else:
        return None

def continue_execution_until_return(p, project, concrete_state, addr):
    simgr = p.factory.simgr(concrete_state)
    exploration = simgr.explore(find=addr)
    if exploration.stashes['found']:
        new_concrete_state = exploration.stashes['found'][0]
        return new_concrete_state
    else:
        return None

def solve_argv(argv_number, argv_size, func_name, stdin_bypass, project, cfg, path_number):
    args = []
    solution_argvs = []
    stdin_input = "None"
    arg_str = ""
    stdin_size = 128
    for i in range(0, argv_number):
        arg_str = "X" * (argv_size)
        args.append(arg_str)
        arg_str = ""
    print(args)
    cp1 = multiprocessing.Process(target=create_ssh_connection, args=(GDB_SERVER_IP, args, stdin_bypass))
    cp1.start()
    time.sleep(2)
    p, state, avatar_gdb = create_concrete_connection(args)
    addr_libc_start_main = getFuncAddress(cfg, '__libc_start_main', plt=True)
    print("-----------------------------------------------------")
    new_concrete_state = execute_concretly(p, state, addr_libc_start_main, [])
    new_symbolic_state = continue_execution_until_return(p, project, new_concrete_state, addr_libc_start_main)
    address = new_concrete_state.mem[new_concrete_state.regs.ecx+4].int.resolved
    '''
    address is holding a pointer to argv[] and as the system is 32 bit we are able to move throw argvs via size_of_input + 1 (!) to address
    ([!] Some changes to angr-dev/angr/angr/storage/memory_mixins/default_filler_mixin.py file in line 16 added 4 new lines accroding to the issues
        marked as [+]/[-] at the end)
    '''
    #argv symbolization
    symbolic_buffer_address = []
    for i in range(0 ,argv_number):
        argv_data = new_concrete_state.mem[address + (i* (argv_size + 1))].uint32_t.resolved
        symbolic_buffer_address.append(address + (i* (argv_size + 1))) ### specify the size of each argv + 1 for symbolization
    arg_sym = []
    arg_name_string = 'arg'
    for i in range(0, argv_number):
        arg_sym.append(claripy.BVS(arg_name_string, argv_size * 8))
        new_concrete_state.memory.store(symbolic_buffer_address[i], arg_sym[i])
    
    result = solve(p, project, func_name, new_concrete_state, symbolic_buffer_address, arg_sym, cfg, path_number)
    if result != None:
        print(result)
        #kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
        solved_args, solution_argvs,new_symbolic_state, func_addr = result
    else:
        print("[" + func_name + "] no path available")
        avatar_gdb.shutdown()
        cp1.join()
        return None
    return (p, project, avatar_gdb, cp1, new_concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr)

def solve_stdin(p, avatar_gdb, cp1, project, cfg, path_number, func_name, concrete_state, symbolic_buffer_address, stdin_size=10):
    stdin_sym = []
    stdin_name_string = "stdin"
    for i in range(0, len(symbolic_buffer_address)):
        stdin_sym.append(claripy.BVS(stdin_name_string, stdin_size * 8))
        concrete_state.memory.store(symbolic_buffer_address[i], stdin_sym[i])
    
    result = solve(p, project, func_name, concrete_state, symbolic_buffer_address, stdin_sym, cfg, path_number)
    if result != None:
        print(result)
        #kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
        solved_stdin, solution_stdin,new_symbolic_state, func_addr = result
    else:
        print("[" + func_name + "] no path available")
        avatar_gdb.shutdown()
        cp1.join()
        return None
    return (p, project, cp1, avatar_gdb, concrete_state, solved_stdin, solution_stdin, new_symbolic_state, func_addr)



def fuzzing_engine(solved_argvs, solved_stdins, argv_number, mode, test_unit_name, info):
    global CRASH_COUNTER
    global MAX_FUZZ_SIZE
    print("[+] Fuzzing with solved argvs and stdins")
    size = 10
    print(solved_argvs)
    print(solved_stdins)
    print("---------------------------")
    if mode == "argv":
        for i in range(0, argv_number):
            size = 10
            while size <= MAX_FUZZ_SIZE:
                clear_status(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                size *=10
                #here we need to call fuzzing function for the target using python lib ssh
                ssh_fuzzing(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME, solved_argvs,
                solved_stdins, size, "argv", i)

                time.sleep(1)
                running_flag = check_program_running(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                if running_flag == 1:
                    kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                    print("[-] Program is not running!")
                    break
                else:
                    crash_status, exit_signal = check_program_status(GDB_SERVER_IP, SSH_USERNAME,
                    SSH_PASSWORD, PROGRAM_NAME)

                    if crash_status == 1:
                        print(colored('[++] Program ended and Program crash with status code: ', 'red', attrs=['reverse', 'blink']),  exit_signal)
                        report_export(REPORT_FILENAME, CRASH_COUNTER, list_to_str(solved_argvs), solved_stdins, size, mode, i, test_unit_name, exit_signal, info)
                        CRASH_COUNTER +=1
                        break
                    elif crash_status == 0:
                        print("[-] Program ended and no crash founded")
                clear_status(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
    if mode == "stdin":
        i = 0
        stdin_fuzz_round = 0
        if len(solved_stdins)==0:
            stdin_fuzz_round =1
        else:
            stdin_fuzz_round = len(solved_stdins) 
        while i < stdin_fuzz_round:
            size = 10
            while size <= MAX_FUZZ_SIZE:
                clear_status(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                size *=10
                #here we need to call fuzzing function for the target using python lib ssh
                ssh_fuzzing(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME, solved_argvs,
                solved_stdins, size, "stdin", i)

                time.sleep(1)
                running_flag = check_program_running(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)

                if running_flag == 1:
                    kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                    print("[-] Program is not running!")
                    break
                else:
                    crash_status, exit_signal = check_program_status(GDB_SERVER_IP, SSH_USERNAME,
                    SSH_PASSWORD, PROGRAM_NAME)

                    if crash_status == 1:
                        print(colored('[++] Program ended and Program crash with status code: ', 'red', attrs=['reverse', 'blink']),  exit_signal)
                        report_export(REPORT_FILENAME, CRASH_COUNTER, list_to_str(solved_argvs), solved_stdins, size, mode, i,test_unit_name, exit_signal, info)
                        CRASH_COUNTER +=1
                        break
                    elif crash_status == 0:
                        print("[-] Program ended and no crash founded")
                clear_status(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
            i+=1
def get_function_calls(project, cfg, func_name):
    target_address = getListAddressOfFunctionCall(project, cfg, func_name)
    return target_address

def try_reach(p, avatar_gdb, new_symbolic_state, addr, solved_args):
    concrete_state = execute_concretly(p, new_symbolic_state, addr, solved_args)
    return concrete_state

def handler(signum, frame):
    raise Exception("notReachable")

def analyzer(argv_number, argv_size, test_unit_name, mode="both"):
    function_target = 0
    path_stack = []
    path_number = 0
    print("[+] Test unit: " + test_unit_name)
    project = angr.Project(binary_x86, load_options={'auto_load_libs':False})
    cfg = project.analyses.CFGFast(data_references=True)
    if mode!="stdin":
        for i in range(function_target, len(sus_function_argv)):
            print("[+] Check Suspecious function: " + sus_function_argv[function_target])
            max_func_calls = get_function_calls(project, cfg, sus_function_argv[function_target])
            if len(max_func_calls) == 0:
                function_target += 1
                continue
            path_number = 0
            while path_number < len(max_func_calls):
                set_root_on(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD)
                print("[+] search function name:")
                print(sus_function_argv[function_target])
                p = None
                avatar_gdb = None
                cp1 = None
                new_concrete_state = None
                solved_args = None
                solution_argvs = None
                new_symbolic_state = None
                func_addr = None
                stdin_bypass = ""
                solution_stdin_finall = []
                kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                result = solve_argv(argv_number, argv_size, sus_function_argv[function_target], stdin_bypass, project, cfg, path_number)
                if result != None:
                    p, project, avatar_gdb, cp1, new_concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr = result
                    info = {}
                    info['func_name'] = sus_function_argv[function_target]
                    info['func_addr'] = max_func_calls[path_number]
                    fuzzing_engine(solution_argvs, solution_stdin_finall, argv_number, "argv", test_unit_name, info)
                    avatar_gdb.shutdown()
                    cp1.join()
                    #due to path finding problems execute concerete till target adderss
                    path_number += 1
                else:
                    #if path_number is 0 that means we need to change the target function else change path_number
                    path_number = 0
                    break
            function_target += 1
    
    function_target = 0
    if mode!="argv":
        for s in range(function_target, len(sus_function_stdin)):
            print("[+] Check Suspecious function: " + sus_function_stdin[s])
            max_func_calls = get_function_calls(project, cfg, sus_function_stdin[s])
            if len(max_func_calls) == 0:
                continue
            set_root_on(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD)
            original_sigalarm_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, handler)
            path_number = 0
            stdin_symbolic_buffer_address = []
            solution_stdin_finall = []
            
            stdin_bypass = ""
            stdin_bypass_time = 0
            DONE = False
            while not DONE:
                print(len(max_func_calls))
                if len(path_stack)==0:
                    #20 is optional
                    result = solve_argv(argv_number, argv_size, sus_function_stdin[s], stdin_bypass, project, cfg, path_number)
                    if result != None:
                        p, project, avatar_gdb, cp1, concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr = result
                        
                        reachable = False
                        signal.alarm(3)
                        try:
                            concrete_state = try_reach(p, avatar_gdb, new_symbolic_state, func_addr, solved_args)
                            print("[+] reached!")
                            reachable = True
                        except Exception:
                            print("[-] Not reachable")
                            reachable = False
                        signal.alarm(0)
                        avatar_gdb.shutdown()
                        cp1.terminate()
                        cp1.join()
                        kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, "gdbserver")
                        kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                        signal.signal(signal.SIGALRM, original_sigalarm_handler)
                        if reachable:
                            info = {}
                            info['func_name'] = sus_function_stdin[s]
                            info['func_addr'] = max_func_calls[path_number]
                            fuzzing_engine(solution_argvs, solution_stdin_finall, argv_number, "stdin", test_unit_name, info)
                            path_stack.append(path_number)
                            stdin_bypass_time += 1
                            stdin_bypass = stdin_bypass_time * "A\n"
                        path_number += 1
                else:
                    #while till reach the fuzz point and solve args and stdins
                    index = 0
                    while len(path_stack):
                        result = solve_argv(argv_number, argv_size, sus_function_stdin[s], stdin_bypass, project, cfg, path_stack[index])
                        if result!=None:
                            p, project, avatar_gdb, cp1, concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr = result
                            
                            concrete_state = try_reach(p, avatar_gdb, new_symbolic_state, max_func_calls[path_stack[index]] + 0x5, solved_args)
                            stdin_buff_address = getBufferAddress(concrete_state)
                            
                            new_symbolic_state = continue_execution_until_return(p, project, new_symbolic_state, max_func_calls[0] + 0x5)
                            stdin_symbolic_buffer_address = []
                            stdin_symbolic_buffer_address.append(stdin_buff_address)
                            index += 1
                            path_stack = path_stack[1:]
                            if len(path_stack)==0:
                                for i in range(0, len(max_func_calls)):
                                    result = solve_stdin(p, avatar_gdb, cp1, project, cfg, i, sus_function_argv[1], concrete_state, stdin_symbolic_buffer_address)
                                    if result != None:
                                        p, project, avatar_gdb, cp1, concrete_state, solved_stdins, solution_stdins, new_symbolic_state, func_addr = result
                                        info = {}
                                        info['func_name'] = sus_function_argv[1]
                                        info['func_addr'] = max_func_calls[i]
                                        fuzzing_engine(solution_argvs, solution_stdins, argv_number, "stdin", test_unit_name, info)
                                        break
                                    else:
                                        print("[-] try another...")
                                DONE = True
                                break
    
    return None

if __name__ == "__main__":
    '''
        After setup its better run automation.py
        change ARGV_NUM and ARGV_SIZE in automation to get better analysis
    '''
    if len(sys.argv) < 3:
        print("[-] Execute like: $python symdynfuzz.py <argv_num> <argv_size> [<|stdin|argv|>]*")
        exit(2)
    if len(sys.argv) < 4:
        analyzer(int(sys.argv[1]), int(sys.argv[2]), "test001")
    else:
        analyzer(int(sys.argv[1]), int(sys.argv[2]), "test001", str(sys.argv[3]))
