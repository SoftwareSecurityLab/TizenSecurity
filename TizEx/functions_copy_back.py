from shared import *
from variable_declaration import *
from functions import *


def get_variables_declared(line):
    # takes a line returns the variables declared here
    # e.g: var a, b -> ['a', 'b']
    # var a = 10; ->['a']

    if not (line.startswith('var') or line.startswith('let') or line.startswith('const')):
        # not a variable declaration
        return []

    if line.startswith('var') or line.startswith('let'):
        line = line[4:]
    elif line.startswith('const'):
        line = line[6:]
    else:
        # not a variable declaration
        return []
    
    # first we separate variables with ','line
    # but maybe there are other ','s. e.g: var a = foo(x, y, z)
    # replace function args with '' 
    while line.find('(') != -1:
        start_idx = line.index('(')
        _, end_idx = balance_pairs([], line, '(', ')')
        line = line[:start_idx] + line[end_idx + 1:]

    vars = line.split(',')
    variable_regex = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
    for i in range(len(vars)):
        vars[i] = vars[i].strip()
        tmp_idx = variable_regex.search(vars[i])
        s, e = tmp_idx.span()
        vars[i] = vars[i][s:e + 1].strip()

    return vars


def copy_back(file_in, file_out, entry_points, func_calls):
    # function bodies are stored in a temporary file
    # copying them back in the main file
    brace_balance = 0

    tmp_entry_points = entry_points.copy()
    for line in file_in:
        line = line.strip()
        
        line = line.replace('.json()', '')

        if 'fetch' in line:
            tmp_line = line
            line = re.sub(r'\bfetch\(', 'fetch({},', line)
            tmp_line = re.sub(r'\bfetch\(', 'fetch([],', line)
            line = line + tmp_line

        brace_balance += line.count('{')   # according to how functions are stored, in starting function line there should be only one '{'
        brace_balance -= line.count('}')   # and closing function braces is in a new line alone
        if brace_balance == 0:
            tmp_entry_points = entry_points.copy()
        if line.startswith('function '):
            end_prototype_idx = line.index('(')   # according to how functions are copied there, there should be a '(' in this line
            function_name = line[9:end_prototype_idx]

            entry_args = func_calls.get(function_name, [])
            start_idx_args = line.index('(') + 1
            end_idx_args = line.index(')')
            
            function_args = line[start_idx_args:end_idx_args]
            function_args = function_args.strip().split(',')
            
            for item in entry_args:
                tmp_entry_points.append(function_args[item - 1].strip())
            
        
        variables = get_variables_declared(line)
        for variable in variables:
            if variable in tmp_entry_points:
                tmp_entry_points.remove(variable)
        
        if line.strip().startswith('//'):
            continue
        decalre_res = handle_variable_declaration(line, declare_reg, tmp_entry_points, file_in, file_out)
        if not decalre_res:
            print(line, file=file_out)

        handle_function_call(line, func_call_regex, entry_points, func_calls)


            
            

