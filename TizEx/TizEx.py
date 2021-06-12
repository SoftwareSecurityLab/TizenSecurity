import argparse
import subprocess
from variable_declaration import *
from functions import *
from shared import *
from html5print import JSBeautifier
from function_call import * 
from functions_copy_back import *

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

    initial_code = '''
    var S$ = require('S$');\n
    class element {
        constructor(name) {
            this.name = name;
            this.innerHTML = new S$.symbol(name + 'html', '');
            this.innerText = new S$.symbol(name + 'text', '');
        }
        addEventListener(event, f) {
            f(S$.symbol(this.name + event, {}));
        }
    }

    document = {
        getElementById: function (name) {
            return new element(name);
        }
    }\n 
    class Promise {
        static increaseCount() {
            this.count++;
        }

        constructor(callBack, init='') {
            Promise.increaseCount();
            this.status = Array();
            function resolved(a) {
                this.status.push('fullfilled');
                this.resolved_return = a;
            }

            function rejected(a) {
                this.status.push('rejected');
                this.rejected_return = a;
            }
            this.resolved_bind = resolved.bind(this);
            this.rejected_bind = rejected.bind(this);
            this.result = S$.symbol('Promise' + Promise.count, init);
            callBack(this.resolved_bind, this.rejected_bind);
            this.final_status = this.status[0];
        }

        then(onSuccess, onFailure=undefined){
            if (this.final_status == 'fullfilled') {
                onSuccess(this.result);
            } else {
                onFailure(this.result);   // there will be an error if onFailure is not defined!
            }
            return this;
        }

    };
    Promise.count = 0;

    function fetch(type, url) {
        if (!isEquivalent({}, type) && !isEquivalent('', type) && !isEquivalent(type, []) && !typeof type === 'number' && !typeof type === 'boolean' && !typeof type == 'undefined') {
            type = {};
        }
        return new Promise(function(res, rej) {
            res('abc');
            rej('def');
        }, type)
    }

    function isEquivalent(a, b) {
        // Create arrays of property names
        var aProps = Object.getOwnPropertyNames(a);
        var bProps = Object.getOwnPropertyNames(b);

        // If number of properties is different,
        // objects are not equivalent
        if (aProps.length != bProps.length) {
            return false;
        }

        for (var i = 0; i < aProps.length; i++) {
            var propName = aProps[i];

            // If values of same property are not equal,
            // objects are not equivalent
            if (a[propName] !== b[propName]) {
                return false;
            }
        }

        // If we made it this far, objects
        // are considered equivalent
        return true;
    }
    '''
    
    # beautifying code
    subprocess.run(f'html5-print -t js -o tmp {fin.name}'.split())

    print(initial_code, file=fout)
     


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

    init(file_in, file_out)  # this function creates a tmp file which beautified version of original code

    file_in_tmp = open(input_tmp_file, 'r') 

    entry_points = ['document']  # can have other variables
    func_calls = dict()
    # status = True


    for line in file_in_tmp:
        # for each line in js code
        # it is assumed JS code is a pretty code

        # line = line.split('=')
        # declaration_result = declare_reg.match(line):
        # if declaration_result:
            # declaration statement
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
    file_in_tmp.close()
    os.remove(input_tmp_file)
    functions_tmp.close()
    functions_tmp = open(functions_tmp_file_name)

    copy_back(functions_tmp, file_out, entry_points, func_calls)   # copying back functions



    print(entry_points)

    print(func_calls)
    print(new_file_name)
    file_out.close()
    os.remove(functions_tmp_file_name)

    # subprocess.run(['../expoSE', new_file_name])


    



