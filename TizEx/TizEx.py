import argparse
import subprocess
from variable_declaration import *
from functions import *
from shared import *
from html5print import JSBeautifier 

# TODO:
# 1. fixing the method of saving JS varirables
# 2. adding other JS objects like window
# 3. handling functions and function variables 
# 4. handling fetch and ajax and ... functions
# 5. make JS code beautiful before parsing 


# TODO:
# 1. delete temp files. (tmpfiles for funcs and ...) 

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

def init(fin, fout):
    # fin is the file handler of input stream
    # fout is the file handler of output stram

    # writing initial objects to f 
    if not isinstance(fin, io.IOBase) or not isinstance(fout, io.IOBase):
        raise ValueError('f must be a file!')

    initial_code = (
        "var S$ = require('S$');\n"
        'document = {',
        '   getElementById: function (name) {',
        '       return S$.symbol(name, {});',
        '   }',
        '}'
    )

    
    # beautifying code
    subprocess.run(f'html5-print -t js -o tmp {fin.name}'.split())

    print('\n'.join(initial_code), file=fout)
     


if __name__ == '__main__':
    file_path = get_args()  # path to the file
    file_path_ext = os.path.splitext(file_path)
    new_file_name = file_path_ext[0] + '_test' + file_path_ext[1]  # new file path to write in
    # input_tmp_file = file_path_ext[0] + '_input_test' + file_path_ext[1]  
    input_tmp_file = 'tmp'   # original JS code is first beautified and copied in this file
    functions_tmp_file_name = file_path_ext[0] + '_test_temp_funcs' + file_path_ext[1] 

    file_in = open(file_path, 'r')   # original file
    file_out = open(new_file_name, 'w')    # new file
    functions_tmp = open(functions_tmp_file_name, 'w')

    init(file_in, file_out)

    file_in_tmp = open(input_tmp_file, 'r') 

    entry_points = ['document']  # can have other variables
    status = True

    variable_declaration_pattern = r'\s*(var |let |const )?(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\'\(\)]*)(\s*=\s*([^,;])*)?\s*,)*(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\(\)\']*)(\s*=\s*([^,;])*)?\s*);'
    assigned_function_pattern = r'\s*(var |let |cont )?\s*\S+\s*=\s*function\s*'
    normal_function_pattern = r'\s*function\s+\w+\s*\([^)]*\)'

    declare_reg = re.compile(variable_declaration_pattern) 
    assigned_func_reg = re.compile(assigned_function_pattern)
    normal_func_reg = re.compile(normal_function_pattern)

    for line in file_in_tmp:
        # for each line in js code
        # it is assumed JS code is a pretty code

        # line = line.split('=')
        # declaration_result = declare_reg.match(line):
        # if declaration_result:
            # declaration statement
        
        decalre_res = handle_variable_declaration(line, declare_reg, entry_points, file_in_tmp, file_out)
        func_res = handle_functions(line, assigned_func_reg, normal_func_reg, file_in_tmp, file_out, functions_tmp)

        if func_res:
            pass
        elif decalre_res:
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
    file_in_tmp.close()
    # os.remove(input_tmp_file)

    print(entry_points)

    print(new_file_name)

    # subprocess.run(['../expoSE', new_file_name])


    



