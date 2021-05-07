import argparse
import subprocess
from variable_declaration import *
from functions import *
from shared import *

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
     


if __name__ == '__main__':
    file_path = get_args()  # path to the file
    file_path_ext = os.path.splitext(file_path)
    new_file_name = file_path_ext[0] + '_test' + file_path_ext[1]  # new file path to write in
    functions_tmp_file_name = file_path_ext[0] + '_test_temp_funcs' + file_path_ext[1] 

    file_in = open(file_path, 'r')   # original file
    file_out = open(new_file_name, 'w')    # new file
    functions_tmp = open(functions_tmp_file_name, 'w') 

    init(file_out)

    entry_points = ['document']  # can have other variables
    status = True

    variable_declaration_pattern = r'\s*(var |let |const )?(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\'\(\)]*)(\s*=\s*([^,;])*)?\s*,)*(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\(\)\']*)(\s*=\s*([^,;])*)?\s*);'
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

    print(new_file_name)

    subprocess.run(['../expoSE', new_file_name])


    



