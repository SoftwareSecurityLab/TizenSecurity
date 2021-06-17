import argparse
import subprocess
from variable_declaration import *
from functions import *
from shared import *
from html5print import JSBeautifier
from function_call import * 
from functions_copy_back import *
from html_events import *
from init import *
from bs4 import BeautifulSoup
import requests

# TODO:
# 1. fixing the method of saving JS varirables
# 2. adding other JS objects like window
# 3. handling functions and function variables 
# 4. handling fetch and ajax and ... functions
# 5. make JS code beautiful before parsing 


# TODO:
# 1. delete temp files. (tmpfiles for funcs and ...) 

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', help='path to HTML file.', dest='html')
    parser.add_argument('--js', help='path to JS file. Ignored if --html is specified.', dest='js')
    parser.add_argument('--cdns', help='specifying cdns to not to check them. list their index in html file starting at 0', dest='cdns', nargs='*', default=[])
    args = parser.parse_args()
    
    if args.html:
        extract_call_backs_html(args.html) # extracts all bounded callback functions in html such as onclick. saves them to a file.
        soup = BeautifulSoup(open(args.html), 'html.parser')
        scripts = soup.select('script')
    elif args.js:
        scripts = [args.js]

    return scripts, args.cdns

def copy_file_to_file(from_handler, to_handler):
    # gets two handlers of files. copies contents of the first one to second
    for line in from_handler:
        print(line, file=to_handler, end='')
     

scripts, cdns = get_args()
output_file_name = 'Tizex_analyze.js'
file_out = open(output_file_name, 'w')    # new file
output_file = open(output_file_name, 'w')
init(file_out)  # this function creates a tmp file which beautified version of original code

for i in range(len(scripts)):
    script = scripts[i]
    if i in cdns:
        if type(script) == str:
            # when only js file is specified in args type of script is string
            f = open(script)
            for line in f:
                print(line, file=output_file)
        elif script.attrs.get('src'):
            # beautifulSoup obj. a script with src attribute.
            src = script.attrs.get('src')
            if src.startswith('http'):
                response = requests.get(src).text
                print(response, file=output_file)
            else:
                for line in open(src):
                    print(line, file=output_file)
        else:
            # beautifulSoup objec. a script with code inside a script tag in html
            print(script.text, file=output_file)
    else:
        temporary_file_name = 'temporary_file.js'  # a temporary file for scripts with src
        temporary_file = open(temporary_file_name, 'w')
        if type(script) == str:
            # script is a path to js file
            for line in open(script):
                print(line, file=temporary_file)
        elif script.attrs.get('src'):
            # script is a bs obj with src
            src = script.attrs['src']
            if src.startswith('http'):
                response = requests.get(src).text
                print(response, file=temporary_file)
            else:
                for line in open(src):
                    print(line, file=temporary_file)
        else:
            # a script without any src. js code is inside the element
            print(script.decode_contents(), file=temporary_file)

        temporary_file.close()
        file_path = temporary_file_name
        # input_tmp_file = file_path_ext[0] + '_input_test' + file_path_ext[1]  
        input_tmp_file = 'tmp'   # original JS code is first beautified and copied in this file
        functions_tmp_file_name = 'TizexAnalyze_functions_tmp'

        file_in = open(file_path, 'r')   # original file
        functions_tmp = open(functions_tmp_file_name, 'w')

        # beautifying code
        subprocess.run(f'html5-print -t js -o tmp {file_in.name}'.split())

        file_in_tmp = open(input_tmp_file, 'r') 

        entry_points = ['document']  # can have other variables
        func_calls = dict()
        # status = True


        for line in file_in_tmp:
            # for each line in js code
            # it is assumed JS code is a pretty code

            line = line.replace('.json()', '')

            if 'fetch' in line:
                tmp_line = line
                line = re.sub(r'\bfetch\(', 'fetch({},', line)
                tmp_line = re.sub(r'\bfetch\(', 'fetch([],', tmp_line)
                line = line + '\n' + tmp_line

            if line.strip().startswith('//'):
                continue
            decalre_res = handle_variable_declaration(line, declare_reg, entry_points, file_in_tmp, file_out)
            func_res = handle_functions(line, assigned_func_reg, normal_func_reg, file_in_tmp, file_out, functions_tmp, func_calls, func_call_regex, entry_points)
            if func_res:
                pass
            elif decalre_res:
                pass
            else:
                print(line, file=file_out)

            handle_function_call(line, func_call_regex, entry_points, func_calls)
        

        file_in.close()
        file_in_tmp.close()
        os.remove(input_tmp_file)
        functions_tmp.close()
        functions_tmp = open(functions_tmp_file_name)

        copy_back(functions_tmp, file_out, entry_points, func_calls)   # copying back functions

events_file = open(event_file_path)
copy_file_to_file(events_file, file_out)
events_file.close()
os.remove(event_file_path)

        
file_out.close()

    






