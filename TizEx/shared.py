import os
import io
import re

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


def create_condition_to_check_injection(var):
    conditional = (
        f'if (String({var}) == "<script>alert(1)</script>") {{',
        '   throw new Error("XSS!");',
        '}\n'
    )
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