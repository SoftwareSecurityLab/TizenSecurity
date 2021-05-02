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
     

def handle_variable_declaration(declaration_string, regex_declaration, entry_points):
    # params:
    # declaration_string is a string of JS variable declaration: e.g: var a, b = c = 30, d;
    # regex_declaration is a compiled regex object with pattern of declaration variables in JS
    # entry_points is a list of strings of variables which are possibly the entrypoint of code, e.g: document
    
    assert(type(regex_declaration) == re.Pattern)
    assert(type(declaration_string) == str)

    match_result = regex_declaration.match(declaration_string)
    if not match_result:
        # not a declaration statement
        return None
    
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
    return to_print + '\n' + conditional_string



if __name__ == '__main__':
    file_path = get_args()  # path to the file
    file_path_ext = os.path.splitext(file_path)
    new_file_name = file_path_ext[0] + '_test' + file_path_ext[1]  # new file path to write in

    file_in = open(file_path, 'r')   # original file
    file_out = open(new_file_name, 'w')    # new file 

    init(file_out)

    entry_points = ['document']  # can have other variables
    status = True

    variable_declaration_pattern = \
        r'\s*(var |let |const )?(\S*\s*=\s*\S*)*;'

    declare_reg = re.compile(variable_declaration_pattern)  # regex object for variable declaration

    for line in file_in:
        # for each line in js code
        # it is assumed JS code is a pretty code

        # line = line.split('=')
        # declaration_result = declare_reg.match(line):
        # if declaration_result:
            # declaration statement
        
        decalre_res = handle_variable_declaration(line, declare_reg, entry_points)
        if decalre_res:
            print(decalre_res, file=file_out)
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

    subprocess.run(['./expoSE', new_file_name])


    



