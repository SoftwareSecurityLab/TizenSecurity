from shared import *

def handle_function_call(line, func_call_regex, entry_points, func_calls):
    # gets a line which has a function call in it.
    # checks whether it has an entry_point or a function call as input or not
    # if so, then this function adds the name of the function to func_calls (which should be a dict)
    # as a key and a list as the value and appends argument number to the list
    # returns a string in which function calls are replaced with '**'
    # e.g: 
    # line: fun1(a, document.getElementById('theId'), fun2(fun3(b), c)) 
    # -> adds fun1 to func_calls with value [2, 3]
    # also adds fun2 to func_calls with value [1]
    # returns fun1(a, **, **)
    # 
    # params:
    # line: a string which is a line of JS code
    # func_call_regex: a compiled regex of function call pattern
    # entry_points: a list of entry points
    # func_calls: a dictionary of function names as keys and argument numbers as values 

    assert(type(func_call_regex) == re.Pattern)
    assert(type(line) == str)
    assert(type(entry_points) == list)
    assert(type(func_calls) == dict)

    if not func_call_regex.search(line):
        return None

    stack = list()

    # idx is the start index to search. there may be more than one function call in one line.
    # in this case in order to process the next function calls we keep track of where to start searching.  
    start_idx = func_call_regex.search(line).span()[0]  # first index where match occured
    while func_call_regex.search(line[start_idx:]):
        # according to jsbeautifier fuction calls should end in one line
        status, end_idx = balance_pairs(stack, line[start_idx:], '(', ')')
        end_idx += start_idx
        
        assert(status == True and len(stack) == 0)  # parantheses should get match
        
        # string between start_idx and end_idx is a function call. e.g: fun1(a, b, c)

        start_idx_args = line[start_idx:end_idx + 1].find('(') + start_idx
        func_name = line[start_idx: start_idx_args]

        if func_name in ['if', 'for', 'while']:
            continue
        
        # now string between start_idx_args and end_idx + 1 is function arguments e.g: (a, b, c)

        func_args = line[start_idx_args + 1:end_idx]

        while func_call_regex.search(func_args):
            # there is a function call inside args
            start_idx_inner = func_call_regex.search(func_args).span()[0]
            status, end_idx_inner = balance_pairs(stack, func_args, '(', ')')  # status is a bool
            assert(status == True and len(stack) == 0)
            handle_function_call(func_args[start_idx_inner:end_idx_inner + 1], func_call_regex, entry_points, func_calls)
            func_args = func_args[:start_idx_inner] + '**' + func_args[end_idx_inner + 1:]


        handle_function_call(func_args, func_call_regex, entry_points, func_calls)  # for recursive function calls
        
        func_args = func_args.split(',')
        func_calls[func_name] = func_calls.get(func_name, list())
        for i in range(len(func_args)):
            if func_args[i].strip() == '**':
                if i + 1 not in func_calls[func_name]:
                    func_calls[func_name].append(i + 1)
            elif check_entry_point(entry_points, func_args[i].strip()):
                if i + 1 not in func_calls[func_name]:
                    func_calls[func_name].append(i + 1)

        tmp = func_call_regex.search(line[end_idx + 1:])
        if tmp:
            # if there are other function calls in this line
            start_idx = tmp.span()[0] + end_idx + 1
        else:
            break

        
        



