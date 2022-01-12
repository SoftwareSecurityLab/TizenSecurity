import sys

def report_export(report_file_name, count, argvs, stdins, size):
    stdin_string = ""
    for i in range(0, len(stdins)):
        stdin_string += stdins[i]
        stdin_string += '\n'
    report_file = open(report_file_name, "a")
    report_file.write("Crash " + str(count) + ":\n")
    report_file.write("argvs :\n")
    report_file.write(argvs + "\n")
    report_file.write("stdins:\n")
    report_file.write(stdin_string)
    report_file.write("stdin junk input size: \n")
    report_file.write(str(size) + "\n")
    report_file.write("============================================================\n")
    report_file.close()