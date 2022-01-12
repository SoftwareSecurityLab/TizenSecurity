from shared import *
import functions


def handle_objects(line, fin, fout, ffuncs, entry_points, func_calls):
    # fin is file handler of input file
    # fout is file handler of outputfile
    # ffunc is file handler of function files
    # line is the starting point of object. it should be '{'
    # returns all of object in one line

    assert(line.strip() == '{')   # when beatifying js code start of the object is just a curly brace
    
    stack = ['{']
    res = '{'
    for line in fin:
        status, idx = balance_pairs(stack, line, '{', '}')
        if not stack:
            break
        if method_declaration_regex.match(line):
            # a method is declared
            fun_start_idx = line.rfind('function')

            func_name = create_random_string(8)  # creates an 8 character random string is created to name the anonyomous function
            func_declaration = 'function ' + func_name + line[fun_start_idx+8:]
            status, rest_of_line = functions.handle_functions(func_declaration, assigned_func_reg, assigned_method_reg, normal_func_reg, fin, fout, 
                            ffuncs, func_calls, func_call_regex, entry_points)
            line = line[:fun_start_idx] + func_name + rest_of_line
            stack.remove('{')
            
        res += line
    
    return res, line[idx + 1:]    # it should also return rest of the line to not to miss any thing
   


