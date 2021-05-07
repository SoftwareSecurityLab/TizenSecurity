import re
import io
from shared import *

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