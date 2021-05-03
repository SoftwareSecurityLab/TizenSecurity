import argparse
import os
import io
import re
import subprocess

# TODO:
# 1. fixing the method of saving JS varirables
# 2. adding other JS objects like window
# 3. handling functions and function variables 
# 4. handling fetch and ajax and ... functions
# 5. make JS code beautiful before parsing 


def get_args():
    # 1. getting path to the file
    parser = argparse.ArgumentParser()
    parser.add_argument('filePath')
    file_path = parser.parse_args().filePath
    
    # 2. checking the file path
    if not os.path.isfile(file_path):
        print('[-] Wrong file path!')
        exit(-1)

    return file_path

def init(f):
    # f is a file handler
    # writing initial objects to f 
    if not isinstance(f, io.IOBase):
        raise ValueError('f must be a file!')

    initial_code = (
        "var S$ = require('S$');\n"
        'document = {',
        '   getElementById: function (name) {',
        '       return S$.symbol(name, {});',
        '   }',
        '}'
    )

    print('\n'.join(initial_code), file=f)

def create_condition_to_check_injection(var):
    conditional = (
        f'if (String({var}) == "<script>alert(1)</script>") {{',
        '   throw new Error("XSS!");',
        '}\n'
    )
    return '\n'.join(conditional)

def check_entry_point(entry_points, variable):
    # checks whether variable is in entry_points or belongs to a variable in entry point
    for entry_point in entry_points:
        if entry_point == variable:
            # variable is entrypoint itself
            return True
        if variable.startswith(entry_point + '.'):
            # variable is an attribute of entrypoint
            return True
    
    return False
     

def handle_variable_declaration(declaration_string, regex_declaration, entry_points, fin, fout):
    # params:
    # declaration_string is a string of JS variable declaration: e.g: var a, b = c = 30, d;
    # regex_declaration is a compiled regex object with pattern of declaration variables in JS
    # entry_points is a list of strings of variables which are possibly the entrypoint of code, e.g: document
    # fin is the file handler of input file
    # fout is the file handler of output file 
    
    assert(type(regex_declaration) == re.Pattern)
    assert(type(declaration_string) == str)

    match_result = regex_declaration.match(declaration_string)
    if not match_result:
        # not a declaration statement
        return False
    
    declaration_string = declaration_string.replace(';', '')

    if match_result.group(1):
        # if code starts with var or const or let, remove them. e.g. : var a, b = c = 30, d  ->  a, b = c = 30, d
        declaration_string = declaration_string.replace(match_result.group(1), '')

    # declaration_parts a list of variables declared. e.g: a, b = 30, d  ->  ['a', ' b = c = 30', ' d']
    declaration_parts = declaration_string.split(',')

    # a string of conditions. if an something is assigned to an output entry then 
    conditional_string = ''
    to_print = ''   # string to print in js file

    if match_result.group(1):
        to_print += match_result.group(1)    # adding var or let at first if it was there

    for declaration_part in declaration_parts:
        declaration_part = declaration_part.strip()   # e.g : ' d'  ->  'd'
        variables = declaration_part.split('=')  # split variables according to =, e.g: b = c = 30  -> ['b ', ' c ', ' 30']
        
        for variable in variables[:-1]:
            tmp = variable   # storing variable in tmp. it is used if we want to remove it from list
            variable = variable.strip()
            if check_entry_point(entry_points, variable):
                # remove output entries and make a conditional statement instead
                conditional_string += create_condition_to_check_injection(variables[-1].strip())
                variables.remove(tmp)

        to_print += '='.join(variables)

        # all variables separated with '=' is asssigned to last one. e.g: b and c are assigned to 30
        assigned_to = variables[-1].strip()

        if check_entry_point(entry_points, assigned_to):
            for variable in variables[:-1]:
                variable = variable.strip()
                entry_points.append(variable)
        to_print += ' ,'
        
    to_print = to_print[:-1] + ';'
    print(to_print + '\n' + conditional_string, file=fout)
    return True

def _handle_curly_braces(stack, line):
    # gets a line and a stack. checks the matches between curly braces. e.g:
    # stack=['{', '{']  ,  line='if (a > b) {'    =>   stack changes to ['{', '{', '{']
    # stack=['{', '{']  ,  line='if (a > b) {}'    =>   stack doesn't change
    # stack=['{', '{']  ,  line='} else'    =>   stack changes to ['{']

    open_idx = line.find('{')   
    close_idx = line.find('}')
    
    while open_idx != -1 or close_idx != -1:
        if (open_idx != -1 and close_idx == -1) or (open_idx != -1 and open_idx < close_idx):
            stack.append('{')
            open_idx = line.find('{', open_idx + 1)
        if (open_idx == -1 and close_idx != -1) or (close_idx != -1 and close_idx < open_idx):
            if len(stack) == 0:
                raise ValueError('JS syntax code is wrong!')
            stack.pop(-1)
            if (len(stack) == 0):
                # curly braces match since stack is created
                return True, close_idx
            close_idx = line.find('}', close_idx + 1)

    return False, -1


def handle_functions(line, assigned_func_regex, normal_func_regex, fin, fout, ffuncs):
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
        func_name_idx = line[1].find('function ') + 9
        func_prototype = line[1][: func_name_idx] + func_name + ' ' + line[1][func_name_idx:]
        line = func_prototype

    status, idx = _handle_curly_braces(stack, line)
    if status:
        print(line[:idx + 1], file=ffuncs)
        return True
    else:
        print(line, file=ffuncs)
        

    # storing everything between two { and } in the temp file
    for line in fin:
        status, idx = _handle_curly_braces(stack, line)
        if status:
            # curly braces matched
            print(line[:idx + 1], file=ffuncs)
            break
        else:
            # not matched
            print(line, file=ffuncs)
    return True


if __name__ == '__main__':
    file_path = get_args()  # path to the file
    file_path_ext = os.path.splitext(file_path)
    new_file_name = file_path_ext[0] + '_test' + file_path_ext[1]  # new file path to write in
    functions_tmp_file_name = file_path_ext[0] + '_test_temp' + file_path_ext[1] 

    file_in = open(file_path, 'r')   # original file
    file_out = open(new_file_name, 'w')    # new file
    functions_tmp = open(functions_tmp_file_name, 'w') 

    init(file_out)

    entry_points = ['document']  # can have other variables
    status = True

    variable_declaration_pattern = r'\s*(var |let |const )?(\S*\s*=\s*\S*)*;'
    assigned_function_pattern = r'\s*(var |let |cont )?\s*\S+\s*=\s*function\s*'
    normal_function_pattern = r'\s*function\s+\w+\s*\([^)]*\)'

    declare_reg = re.compile(variable_declaration_pattern) 
    assigned_func_reg = re.compile(assigned_function_pattern)
    normal_func_reg = re.compile(normal_function_pattern)

    for line in file_in:
        # for each line in js code
        # it is assumed JS code is a pretty code

        # line = line.split('=')
        # declaration_result = declare_reg.match(line):
        # if declaration_result:
            # declaration statement
        
        decalre_res = handle_variable_declaration(line, declare_reg, entry_points, file_in, file_out)
        func_res = handle_functions(line, assigned_func_reg, normal_func_reg, file_in, file_out, functions_tmp)

        if decalre_res:
            pass
        elif func_res:
            pass
        else:
            print(line, file=file_out)



        # if len(line) == 1:
        #     print(line[0], file=file_out)
        #     continue
        # for var in entry_points:
        #     if var in line[0]:       # can be much more complex
        #         add_condition_to_check_injection(file_out, line[1].strip().replace(';', ''))
        #         status = False
        #         break
        # for var in entry_points:
        #     if var in line[1]:       # can be much more complex
        #         entry_points.append(line[0].strip())
        #         break
        # if status:
        #     print('='.join(line), file=file_out)
        # status = True

    file_in.close()
    file_out.close()
    print(entry_points)

    # print(new_file_name)

    # subprocess.run(['./expoSE', new_file_name])


    



