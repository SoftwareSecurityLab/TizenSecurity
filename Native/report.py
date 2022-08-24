import sys
from datetime import datetime

def report_timemeasured(report_file_name, tm):
    report_file = open(report_file_name, "a")
    report_file.write("#########################################\n")
    report_file.write("Analyze time: " + str(tm) + "\n")
    report_file.write("#########################################\n")
    report_file.write("============================================================\n")
    report_file.close()
def report_export(report_file_name, counter, argvs, stdins, size, mode, index, test_unit_name, signum, info):
    stdin_string = ""
    for i in range(0, len(stdins)):
        stdin_string += stdins[i]
        stdin_string += '\n'
    report_file = open(report_file_name, "a")
    report_file.write("File: " + test_unit_name + "\n")
    report_file.write("Crash " + "["+ signum + "]" + " number: " + str(counter) + " - \" DateTime: " + str(datetime.now()) + " \"" + ": \n")
    report_file.write("argvs:\n")
    report_file.write("\"" + argvs + "\"" + "\n")
    report_file.write("stdins:\n")
    report_file.write("\"" + stdin_string + "\"" + "\n")
    report_file.write("junk input size:\n")
    report_file.write(str(size) + "\n")
    report_file.write("Fuzz mode = " + mode + "\n")
    report_file.write("Fuzz index = " + str(index) + "\n")
    report_file.write("Suspicious function: [" +str(info['func_name']) + "]\n")
    report_file.write("Suspicious function address: [" +hex(info['func_addr']) + "]\n")
    report_file.close()