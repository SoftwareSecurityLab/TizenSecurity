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

from ssh_fuzz_status import clear_status
from ssh_fuzz_status import ssh_fuzzing
from ssh_fuzz_status import check_program_status
from ssh_fuzz_status import check_program_running
from ssh_fuzz_status import kill_program
from report import report_export


binary_x86 = "test001"
GDB_SERVER_IP = '192.168.1.105'
GDB_SERVER_PORT = 2323
SSH_USERNAME = "Hossein"
SSH_PASSWORD = "*******"
PROGRAM_NAME = "test001"
ENTRY_POINT = 0x0
sus_function_stdin = ['__isoc99_scanf', 'fgets', 'gets']
sus_function_argv = ['strcpy', 'sprintf', 'memcpy', 'strncpy']
PROGRAM_STATUS_FUZZING = ""
REPORT_FILENAME = "CRASH_REPORT"
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
    subprocess.run(["/home/lab-test3/angr_tests/connect_ssh_DESKTOP.sh", ip, arg[:-1]], input=bytes((fuzz_input).encode()))
    #ret subproccess for future reuse and interact with program on the target

def list_to_str(lst):
    arg = ""
    for i in range(0, len(lst)):
        arg += lst[i] + " "
    return arg[:-1]

def getFuncAddress(cfg, funcName, plt=None):
    found = [
        addr for addr,func in cfg.kb.functions.items()
        if funcName == func.name and (plt is None or func.is_plt == plt)
        ]
    if len( found ) > 0:
        print("Found "+funcName+"'s address at "+hex(found[0])+"!")
        return found[0]
    else:
        raise Exception("No address found for function : "+funcName)
    
def getReturnAddress(concrete_state):
    ret_address_symbolic = concrete_state.mem[concrete_state.regs.esp].int.resolved
    #ret_address_concrete = ret_address_symbolic._model_concrete.value
    return ret_address_symbolic

def getBufferAddress(concrete_state):
    stdin_buffer_address_symbolic = concrete_state.mem[concrete_state.regs.esp + 0x4].int.resolved
    #stdin_buffer_address_concrete = stdin_buffer_address_symbolic._model_concrete.value
    return stdin_buffer_address_symbolic

def normalize_solved_string(binary_configuration):
    start = 0
    end = 0
    normalized_result = b''
    for i in range(0, len(binary_configuration)):
        if binary_configuration[i] != 0:
            start = i
            break
    for i in range(0, len(binary_configuration)):
        if binary_configuration[i] != 0:
            end = i
    
    for i in range(0, end + 1):
        if binary_configuration[i] == 0:
            normalized_result += b'X'
        else:
            normalized_result += bytes(chr(binary_configuration[i]).encode())
    return normalized_result


#generalize the function for stdin and solve stdin buffers
def solve(p, project, funcName, concrete_state, symbolic_buffer_address, arg_sym, select_path):
    cfg = project.analyses.CFG(fail_fast=True)
    func_addr = getFuncAddress(cfg, funcName, plt=True)
    simgr = p.factory.simgr(concrete_state)
    #simgr = p.factory.path_group(concrete_state)
    print(simgr)
    exploration = simgr.explore(find=func_addr, num_find = 3)
    solved_item = []
    solved_args = []
    solution_argvs = []
    if exploration.stashes['found']:
        if len(exploration.stashes['found']) > select_path:
            new_symbolic_state = exploration.stashes['found'][select_path]
            for i in range(0, len(symbolic_buffer_address)):
                binary_configuration = new_symbolic_state.solver.eval(arg_sym[i], cast_to=bytes)
                print(binary_configuration)
                binary_configuration = normalize_solved_string(binary_configuration)
                print(binary_configuration)
                binary_configuration_noNull = binary_configuration.replace(b'\x00', b'')
                solution_argvs.append(binary_configuration_noNull.decode('windows-1252'))
                solved_item.append(symbolic_buffer_address[i])
                solved_item.append(arg_sym[i])
                solved_args.append((solved_item))
                solved_item = []
            return (solved_args, solution_argvs, new_symbolic_state, func_addr)
        else:
            return None
    else:
        return None

def continue_execution_until_return(p, project, concrete_state, addr):
    simgr = p.factory.simgr(concrete_state)
    exploration = simgr.explore(find=addr)
    if exploration.stashes['found']:
        new_symbolic_state = exploration.stashes['found'][0]
        return new_symbolic_state
    else:
        return None


def solve_argv(argv_number, argv_size, func_id, select_path, stdin_bypass):
    args = []
    solution_argvs = []
    #just to skip the unwanted stdin functions
    stdin_input = "None"
    arg_str = ""
    stdin_size = 128
    for i in range(0, argv_number):
        arg_str = "X" * (argv_size)
        args.append(arg_str)
        arg_str = ""
    #args = ["XXXXX", "YYYYY", "XXXXX", "XXXXX"]
    print(args)
    cp1 = multiprocessing.Process(target=create_ssh_connection, args=(GDB_SERVER_IP, args, stdin_bypass))
    cp1.start()
    time.sleep(2)
    p, state, avatar_gdb = create_concrete_connection(args)
    project = angr.Project(binary_x86, load_options={'auto_load_libs':False})

    cfg = project.analyses.CFG(fail_fast=True)
    addr_libc_start_main = getFuncAddress(cfg, '__libc_start_main', plt=True)
    print("-----------------------------------------------------")
    new_concrete_state = execute_concretly(p, state, addr_libc_start_main, [])

    address = new_concrete_state.mem[new_concrete_state.regs.ecx+4].int.resolved
    '''
    address is holding pointer to argv[] and as the system is 32 bit we are able to move throw argvs via size_of_input + 1 (!) to address
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

    result = solve(p, project, sus_function_stdin[int(func_id)], new_concrete_state, symbolic_buffer_address, arg_sym, select_path)
    print("AaaaaaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAAaaaaaaaaaaaaaAAAAAAAAAAAAAAAAaaa")
    if result != None:
        solved_args, solution_argvs,new_symbolic_state, func_addr = result
    else:
        return None
    return (p, project, avatar_gdb, cp1, new_concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr)

def solve_stdin(p, project, avatar_gdb,  new_concrete_state, stdin_number, stdin_buffer_address, func_id, select_path):
    symbolic_buffer_address = []
    stdin_size = 20
    stdin_sym = []
    stdin_name_string = 'stdin'
    symbolic_buffer_address.append(stdin_buffer_address)
    stdin_sym.append(claripy.BVS(stdin_name_string, stdin_size * 8))
    new_concrete_state.memory.store(symbolic_buffer_address[0], stdin_sym[0])
    result = solve(p, project, sus_function_argv[int(func_id)], new_concrete_state, symbolic_buffer_address, stdin_sym, select_path)
    print("AaaaaaaaaAAAAAAAAAAAAAAAAAAAAAAAAAAAAaaaaaaaaaaaaaAAAAAAAAAAAAAAAAaaa")
    if result != None:
        solved_stdin, solution_stdin, new_symbolic_state, func_addr = result
    else:
        return None
    return (p, project, avatar_gdb, new_concrete_state, solved_stdin, solution_stdin, new_symbolic_state, func_addr)

def fuzzing_engine(solved_argvs, solved_stdins):
    global CRASH_COUNTER
    print("[+] Using solved")
    size = 10
    print(solved_argvs)
    print(solved_stdins)
    for j in range(0,2):
        size = 10
        for i in range(0, 2):
            clear_status(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
            size *=10
            #here we need to call fuzzing function for the target using python lib ssh
            ssh_fuzzing(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME, list_to_str(solved_argvs),
             solved_stdins, size)

            time.sleep(2)
            running_flag = check_program_running(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
            if running_flag == 1:
                kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
                break
            else:
                crash_status, exit_signal = check_program_status(GDB_SERVER_IP, SSH_USERNAME,
                 SSH_PASSWORD, PROGRAM_NAME)

                if crash_status == 1:
                    print(colored('[++] Program ended and Program crash with status code: ', 'red', attrs=['reverse', 'blink']),  exit_signal)
                    report_export(REPORT_FILENAME, CRASH_COUNTER, list_to_str(solved_argvs), solved_stdins, size)
                    CRASH_COUNTER +=1
                elif crash_status == 0:
                    print("[-] Program ended and no crash founded")

def analyzer(argv_number, argv_size):
    symbolic_argv_address = []
    arg_sym = []
    ret_address_concrete = []
    stdin_bypass = ""
    stdin_number = 0
    select_path = 0
    path_stack = []
    select_number = 0
    solution_argvs = None
    solution_stdin = None
    solution_stdin_finall = []
    fuzz_flag = 0
    path_stack.append(0)
    argv_passed = 0
    p = None
    project = None
    cp1 = None
    new_concrete_state = None
    solved_args = None
    solution_stdin = None
    solved_stdin = None
    fuzzed_stdins = []
    function_target = 1
    while select_number >= 0:
        kill_program(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, PROGRAM_NAME)
        result = solve_argv(argv_number, argv_size, function_target, path_stack[select_number], stdin_bypass)
        if result != None:
            p, project, avatar_gdb, cp1, new_concrete_state, solved_args, solution_argvs, new_symbolic_state, func_addr = result

            if stdin_number == 0:
                print("1===============")
                print(stdin_number)
                print(select_number)
                print(path_stack)
                print(fuzzed_stdins)
                print("1===============")
                solution_stdin_finall = []
                fuzzing_engine(solution_argvs, solution_stdin_finall)
                stdin_number += 1
                stdin_bypass = stdin_number * "A\n"
                argv_passed = 1
                path_stack.append(select_path)
                avatar_gdb.shutdown()
                cp1.join()
                continue
            else:
                argv_passed = 1
                select_number += 1

        else:
            #we need to change the function target
            exit(1)
        if argv_passed == 1:
            while select_number >= 0:
                print("2===============")
                print(stdin_number)
                print(select_number)
                print(path_stack)
                print(fuzzed_stdins)
                print("2===============")
                if select_number >= len(path_stack):
                    select_number = path_stack[-1]
                if argv_passed == 1:
                    print("######################          ############       ################")
                    new_concrete_state = execute_concretly(p, new_symbolic_state, func_addr, solved_args, [])  
                else:
                    new_concrete_state = execute_concretly(p, new_symbolic_state, func_addr, solved_stdin, [])
                ret_address_concrete = getReturnAddress(new_concrete_state)
                print(ret_address_concrete)
                stdin_buffer_address = getBufferAddress(new_concrete_state)
                print(stdin_buffer_address)
                new_symbolic_state_return = continue_execution_until_return(p, project, new_symbolic_state, ret_address_concrete._model_concrete.value)
                if new_symbolic_state_return != None:
                    new_concrete_state = execute_concretly(p, new_symbolic_state_return, ret_address_concrete._model_concrete.value, [], [])
                else:
                    break
                print("----------------")
                print("[Solve stdin with]")
                print(new_concrete_state.regs.eip)
                print(ret_address_concrete)
                print(stdin_buffer_address)
                print("[+++]")
                print(function_target - 1)
                print("[+++]")
                result = solve_stdin(p, project, avatar_gdb, new_concrete_state, stdin_number, stdin_buffer_address, function_target - 1, path_stack[select_number])
                if result != None:
                    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=========")
                    p, project, avatar_gdb, new_concrete_state, solved_stdin, solution_stdin, new_symbolic_state, func_addr = result
                    solution_stdin_finall.append(solution_stdin[0])
                    if solved_stdin != None:
                        if path_stack not in fuzzed_stdins:
                            fuzzing_engine(solution_argvs, solution_stdin_finall)
                            solution_stdin_finall = []
                            path_stack.append(select_path)
                            fuzzed_stdins.append(path_stack[0: len(path_stack)])
                            stdin_number += 1
                            stdin_bypass = stdin_number * "A\n"
                            select_number = path_stack[0]
                            
                            print("3===============")
                            print(stdin_number)
                            print(select_number)
                            print(path_stack)
                            print(fuzzed_stdins)
                            print("3===============")
                            break
                        else:
                            select_number += 1
                            if select_number > len(path_stack):
                                select_number = path_stack[-1]
                            print("4===============")
                            print(stdin_number)
                            print(select_number)
                            print(path_stack)
                            print(fuzzed_stdins)
                            argv_passed = 0
                            print("4===============")
                        
                else:
                    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                    path_stack.pop()
                    path_stack[-1] = path_stack[-1] + 1
                    select_number -= 1
                    stdin_number -= 1
                    stdin_bypass = stdin_number * "A\n"
                    argv_passed = 0
                    print("5===============")
                    print(stdin_number)
                    print(select_number)
                    print(path_stack)
                    print(fuzzed_stdins)
                    print("5===============")
                    if select_number == 1 or select_number == 0:
                        select_number = 0
                        break
        
        avatar_gdb.shutdown()
        cp1.join()
        #solve_stdin(stdin_buffer_address, stdin_number, )
        
        #stack base solution needed for the path that we are tracking on store selected_path
        '''
        -solve argv to reach func
        -fuzz function
        -solve argv, then solve stdin buffer address to reach another func
        -fuzz function
        -solve argv, then solve stdin buffer address and then solve another stdin buffer address to reach func
        -fuzz function
        -...
        -end
        (each function has different return value (except stdin in for loop))
        '''

        print("[[[[[[EIP]]]]]]]")
        print(new_concrete_state.regs.eip)
        ''' (1) run the target to go till the end of the program
            (2) if no crash found: we move on till the next scanf
            (3) if crash found report then dont fuzz the current scanf go concrently
        '''
        # the case is we need to restart the ssh and this time go full fuzzing mode
        

        
        #binary_configuration = new_symbolic_state.solver.eval(arg1, cast_to=bytes)
        #print(binary_configuration)
        #binary_configuration = new_symbolic_state.solver.eval(arg2, cast_to=bytes)
        #print(binary_configuration)
        #new_concrete_state = execute_concretly(p, new_symbolic_state, FUZZING_ADDRESS, [(symbolic_buffer_address, arg0)], [])
        #check for any stdin input like scanf, fgets, gets...
        #addr_printf = getFuncAddress(cfg, '', plt=True)    
    print(colored("(#^ ^) Analyze completed!", 'green'))
if __name__ == "__main__":
    #setup_x64()
    analyzer(int(sys.argv[1]), int(sys.argv[2]))
