from paramiko import SSHClient
from paramiko import AutoAddPolicy
import sys
import os
import time
from symdynfuzz import *
from report import report_timemeasured
REPORT_FILENAME = "CRASH_REPORT.txt"
def create_ssh_client(ip, usr, passwd):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(ip, username=usr, password=passwd)
    return client

def tizen_setup(ip, usr, passwd):
    client = create_ssh_client(ip, usr, passwd)
    stdin, stdout, stderr = client.exec_command("call c:\\tizen-studio\\setup.bat", get_pty=True)
    lines = stdout.readlines()
    client.close()

def PrepareAndAnalayze(ip, usr, passwd, test_dir, compiled_dir, argv_num, argv_size):
    global REPORT_FILENAME
    client = create_ssh_client(ip, usr, passwd)
    stdin, stdout, stderr = client.exec_command("dir " + test_dir)
    list_out = stdout.readlines()[7:-2]
    files = []
    for i in list_out:
        item = i.split(' ')
        files.append(test_dir + "\\" + item[-1][:-2])
    file_index = 0
    client.close()
    while file_index < len(files):
        if os.path.exists("test001"):
            os.remove("test001")
        client = create_ssh_client(ip, usr, passwd)
        client.exec_command("del " + "Documents\\Tizen-workspace\\test001\\src\\test001.c")
        print("copy " + files[file_index] + " " + "Documents\\Tizen-workspace\\test001\\src\\test001.c")        
        client.exec_command("copy " + files[file_index] + " " + "Documents\\Tizen-workspace\\test001\\src\\test001.c")
        time.sleep(1)
        #compile and install program
        stdin, stdout, stderr=client.exec_command("cd c:\\tizen-studio&&compile_install.bat", get_pty=True)
        lines = stdout.readlines()
        print("[+] Program compiled and installed on target")
        #copy binary file into analyzer env
        os.system("sshpass -p \"" + passwd + "\" scp " + usr + "@" + ip + ":" + compiled_dir + "/test001 .")
        print("[+] Binary file copied to analyzed environment")
        #run alanyzer
        start = time.process_time()
        analyzer(argv_num, argv_size, ''.join(files[file_index].split('\\')[-1]), "argv")
        time_measured = time.process_time() - start
        report_timemeasured(REPORT_FILENAME, time_measured)
        file_index += 1


'''
    Note:   [1] Set target machine IP, port address and ssh username and password
    [This system] <---> [Host machine] <--> [Tizen system]
    Tested on:
    (ubuntu 18.1) <---> (Windows 10) <--> (Tizen mobile 6.5)
    (angr-symbion) <---> (sshd and sdb.exe(Tizen communicator)) <--> (gdbserver)
            [2] For test case compilation install Tizen studio and change make rules to suits you analyze
            [3] Setup sshd on Host machine and fireup Tizen system on it as well
            [!] 175 Stackbase and Heapbase Buffer over flow detected from NIST SARD benchmark with 100% accuracy
            [!] CRASH_REPORT file have reproducable crash info that can be used in furture analysis
'''

GDB_SERVER_IP = 'IP.IP.IP.IP'
GDB_SERVER_PORT = 2323
SSH_USERNAME = "username"
SSH_PASSWORD = "pass"
TEST_DIR_BASE = "Documents\\TizenTestFiles\\TestFiles\\"
TEST_DIR = ["StackBasedBoF\\", "HeapBasedBoF\\"]
TEST_FILES_DIR = ["memcpy", "memcpy_int", "memmove", "memmove_int", "strcat", "strcpy"]
COMPILED_PROGRAM_ADDR = "Documents/Tizen-workspace/test001/Debug"
ARGV_NUM = 1
ARGV_SIZE = 100
print(colored("(%~ ~) Analyze started!", 'green'))
for i in range(1, len(TEST_DIR)):
    for j in range(3, len(TEST_FILES_DIR)):
        PrepareAndAnalayze(GDB_SERVER_IP, SSH_USERNAME, SSH_PASSWORD, TEST_DIR_BASE + TEST_DIR[i] + TEST_FILES_DIR[j], 
        COMPILED_PROGRAM_ADDR, ARGV_NUM, ARGV_SIZE)
print(colored("(#^ ^) Analyze completed!", 'green'))

