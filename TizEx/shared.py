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