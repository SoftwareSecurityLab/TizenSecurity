import os
import io
import re
from string import ascii_letters
from string import digits as ascii_digits
from random import choice


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


def create_condition_to_check_injection(var, strings):
    pattern = r'%\$(\d+)\$%'   # pattern which will be replaced in string
    while re.search(pattern, var):
        var = re.sub(pattern, lambda x: strings[int(x.group(1))], var)
        

    conditional = (
        f'if (String({var}).includes("&lt;img src=x onerror=alert(1) /&gt;<img src=x onerror=alert(1) />")) {{',
        '   throw Error("XSS!");',
        '}\n'
    )

    '%$$%',
    return '\n'.join(conditional)


def balance_pairs(stack, line, first, second):
    # gets a line and a stack. checks the matches first and second character. e.g:
    # first='{', second='}' 
    # stack=['{', '{']  ,  line='if (a > b) {'    =>   stack changes to ['{', '{', '{']
    # stack=['{', '{']  ,  line='if (a > b) {}'    =>   stack doesn't change
    # stack=['{', '{']  ,  line='} else'    =>   stack changes to ['{']

    open_idx = line.find(first)   
    close_idx = line.find(second)
    
    while open_idx != -1 or close_idx != -1:
        if (open_idx != -1 and close_idx == -1) or (open_idx != -1 and open_idx < close_idx):
            stack.append(first)
            open_idx = line.find(first, open_idx + 1)
        if (open_idx == -1 and close_idx != -1) or (close_idx != -1 and close_idx < open_idx):
            if len(stack) == 0:
                raise ValueError('JS syntax code is wrong!')
            stack.pop(-1)
            if (len(stack) == 0):
                # curly braces match since stack is created
                return True, close_idx
            close_idx = line.find(second, close_idx + 1)

    return False, -1


def create_random_string(l):
    # l is the length of the random string of characters and digit. its first character will never be a digit
    assert(type(l) == int)
    res = choice(ascii_letters)
    for i in range(l - 1):
        res += choice(ascii_letters + ascii_digits)
    
    return res



variable_declaration_pattern = r'\s*(var |let |const )?(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\'\(\)\"]*)(\s*=\s*([^,;])*)?\s*,)*(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\(\)\'\"]*)(\s*=\s*([^,;])*)?\s*);'
assigned_function_pattern = r'\s*(var |let |cont )?\s*[\w$]+\s*=\s*function\s*'
normal_function_pattern = r'\s*function\s+\w+\s*\([^)]*\)'
functions_call_pattern = r'[a-zA-Z_][a-zA-Z0-9_\[\]\'\".]*\(.*'
assigned_method_pattern = r'(\w+\.\w+)*\s*\=\s*function\(.*' 
anonymous_func_pattern = r'function\(.*\) {'
object_assignment_pattern = r'\s*(var |let |const )?(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\'\(\)\"]*)(\s*=\s*([^,;])*)?\s*,)*(\s*([a-zA-Z_$][a-zA-Z0-9_$.\[\]\(\)\'\"]*)(\s*=\s*([^,;])*)?\s*){'
method_declaration_pattern = r'^\s*\w[\w\d]*\s*:\s*function\s*\([^\)]*\)\s*\{\s*'
# of course this regex doesn't match only function calls part. regular expressions can't match balanced strings
# i.e. function calls must have balanced parantheses.we should check that in the code 

declare_reg = re.compile(variable_declaration_pattern) 
assigned_func_reg = re.compile(assigned_function_pattern)
assigned_method_reg = re.compile(assigned_method_pattern)
normal_func_reg = re.compile(normal_function_pattern)
func_call_regex = re.compile(functions_call_pattern)
anonymous_func_regex = re.compile(anonymous_func_pattern)
object_assignment_regex = re.compile(object_assignment_pattern)
method_declaration_regex = re.compile(method_declaration_pattern)



event_file_path = 'events.js'

