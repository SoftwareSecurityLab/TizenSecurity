import re
import io
from shared import *


def handle_quotes(string):
    # hndles quotes of a string. e.g: string: var a = "abc'de\"fgh"
    # returns  var a = %$$%  and ["abc'de\"fgh"]
    
    status = False # when iterating in string status indicatts current position is in an open quote
    q = None  # if status is true then the q is either ' or " and is the oened quote
    strings = list()  # strings in quotes which are replaced in the main strin
    result = str()    # the result of replacing strings in input string with %$$%

    start = end = None    # start and end index of quotes
    slash_count = 0    # sometimes it is needed to count slashes before quote. e.g: \\\\\' is not a string quote

    for i in range(len(string)):
        if string[i] not in '\'"':
            continue

        j = i   # i is needed
        while j - 1 >= 0 and string[j - 1] == '\\':
            slash_count += 1
            j -= 1

        if slash_count % 2 == 1:
            slash_count = 0
            continue

        if not status:
            status = True
            start = i
            q = string[i]
        elif q == string[i]:
            status = False
            end = i
            strings.append(string[start:end + 1])
            # string = string.replace(string[start:end + 1], '%$$%', 1)
        else:
            # e.g: "abc'dd" when reaching the to '
            continue
    
    i = 0
    res = dict()  # a map from number to a string which will be used to replace a string with that
    for item in strings:
        res[i] = item
        string = string.replace(item, '%$' + str(i) +'$%', 1)
        i += 1
    
    return string, res




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

    # first removing strings. at the end they will be back
    # by removing the strings it is easier to decide about parts of the declaration strings

    # strings_double_q = re.findall(r'"(?:(?:(?!(?<!\\)").)*)"', declaration_string)
    # for string in strings_double_q:
    #     declaration_string = declaration_string.replace(string, '##', 1)

    # strings_single_q = re.findall(r"'(?:(?:(?!(?<!\\)').)*)'", declaration_string)
    # for string in strings_single_q:
    #     declaration_string = declaration_string.replace(string, '%%', 1)

    declaration_string, strings = handle_quotes(declaration_string)

    # declaration_parts a list of variables declared. e.g: a, b = 30, d  ->  ['a', ' b = c = 30', ' d']
    declaration_parts = declaration_string.split(',')

    # a string of conditions. if an something is assigned to an output entry then 
    conditional_string = ''
    to_print = ''   # string to print in js file

    if match_result.group(1):
        to_print += match_result.group(1)    # adding var or let at first if it was there

    for declaration_part in declaration_parts:
        declaration_part = declaration_part.strip()   # e.g : ' d'  ->  'd'
        
        declaration_part = declaration_part.replace('==', '%^%')  # there will be a problem when splitting the string with =.

        variables = declaration_part.split('=')  # split variables according to =, e.g: b = c = 30  -> ['b ', ' c ', ' 30']
        
        for i in range(len(variables)):  # replacing %^% with ==
            variables[i] = variables[i].replace('%^%', '==')

        for variable in variables[:-1]:
            tmp = variable   # storing variable in tmp. it is used if we want to remove it from list
            variable = variable.strip()
            if check_entry_point(entry_points, variable):
                # remove output entries and make a conditional statement instead
                conditional_string += create_condition_to_check_injection(variables[-1].strip(), strings)
                variables.remove(tmp)

        to_print += '='.join(variables)

        # all variables separated with '=' is asssigned to last one. e.g: b and c are assigned to 30
        assigned_to = variables[-1].strip()

        if check_entry_point(entry_points, assigned_to):
            for variable in variables[:-1]:
                variable = variable.strip()
                entry_points.append(variable)
        to_print += ' ,'

    # for string in strings_double_q:
    #     to_print = to_print.replace('##', string, 1)
    
    # for string in strings_single_q:
    #     to_print = to_print.replace('%%', string, 1)
        
    pattern = r'%\$(\d+)\$%'   # pattern which will be replaced in string
    while re.search(pattern, to_print):
        to_print = re.sub(pattern, lambda x: strings[int(x.group(1))], to_print)

    to_print = to_print[:-1] + ';'
    print(to_print + '\n' + conditional_string, file=fout)
    return True