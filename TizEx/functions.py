import re
import io
from shared import *
from function_call import *


def handle_functions(line, assigned_func_regex, normal_func_regex, fin, fout, ffuncs, func_calls, func_call_regex, entry_points):
    # params:
    # line: current line which is reading from input file
    # assigned_func_regex: a compiled regex for functions that are assigned to a variable: e.g var a = function(){} 
    # normal_func_regex: a compiled regex for functions that are decalred: e.g function foo() {}
    # entry_points: a list of entrypoints
    # fin: file handler of input file
    # fout: file handler of output file
    # ffuncs: file handler to store functions temporarily
    

    # in order to handle function arguments which may be entry points we first store all functions
    # in a temp file and add them at last of the code
    # also when a function is assigned to a variable we change the prototype of the function. e.g:
    # var a = function () {}  ->   function a () {} 

    assert(type(assigned_func_regex) == re.Pattern)
    assert(type(normal_func_regex) == re.Pattern)
    assert(isinstance(fin, io.IOBase))
    assert(isinstance(fout, io.IOBase))

    if not assigned_func_regex.match(line) and not normal_func_regex.match(line):
        return False

    stack = list()  # is used to match curly braces

    if assigned_func_regex.match(line):
        line = re.sub(r'^\s*(var |const |let )', '', line)
        line = line.split('=')
        func_name = line[0].strip()
        func_name_idx = line[1].find('function') + 8
        func_prototype = line[1][: func_name_idx] + ' ' + func_name + line[1][func_name_idx:]
        line = func_prototype

    status, idx = balance_pairs(stack, line, '{', '}')
    if status:
        print(line[:idx + 1], file=ffuncs)
        return True
    else:
        print(line, file=ffuncs)
        

    # storing everything between two { and } in the temp file
    for line in fin:
        handle_function_call(line, func_call_regex, entry_points, func_calls)
        status, idx = balance_pairs(stack, line, '{', '}')
        if status:
            # curly braces matched
            print(line[:idx + 1], file=ffuncs)
            break
        else:
            # not matched
            print(line, file=ffuncs)
    return True