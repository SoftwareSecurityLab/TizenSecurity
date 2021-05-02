import argparse
import os
import io
import re
import subprocess

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

def add_condition_to_check_injection(f, var):
    conditional = (
        f'if (String({var}) == "<script>alert(1)</script>") {{',
        '   throw new Error("XSS!")',
        '}'
    )
    print('\n'.join(conditional), file=f)


file_path = get_args()  # path to the file
file_path_ext = os.path.splitext(file_path)
new_file_name = file_path_ext[0] + '_test' + file_path_ext[1]  # new file path to write in

file_in = open(file_path, 'r')   # original file
file_out = open(new_file_name, 'w')    # new file 

init(file_out)

suspicious_vars = ['document']  # can have other variables
status = True

for line in file_in:
    line = line.split('=')
    if len(line) == 1:
        print(line[0], file=file_out)
        continue
    for var in suspicious_vars:
        if var in line[0]:       # can be much more complex
            add_condition_to_check_injection(file_out, line[1].strip().replace(';', ''))
            status = False
            break
    for var in suspicious_vars:
        if var in line[1]:       # can be much more complex
            suspicious_vars.append(line[0].strip())
            break
    if status:
        print('='.join(line), file=file_out)
    status = True

file_in.close()
file_out.close()

print(new_file_name)

subprocess.run(['./expoSE', new_file_name])


    



