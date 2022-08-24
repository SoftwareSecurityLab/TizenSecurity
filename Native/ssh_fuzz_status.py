from paramiko import SSHClient
from paramiko import AutoAddPolicy
import sys

TOOL_SDB_ADDR = 'c:\\tizen-studio\\tools\\'

def check_program_status(ip,usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR +'sdb.exe shell /usr/bin/dmesg')
	list_out = stdout.readlines()
	status_crash = 0
	code_crash = ""
	for item in list_out:
		if "segfault" in item and name in item:
			status_crash = 1
			code_crash = "SIGSEGV"
	for item in list_out:
		if "sig=6" in item and name in item:
			status_crash = 1
			code_crash = "SIGABORT"
	client.close()
	return (status_crash, code_crash)

def clear_status(ip,usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR + 'sdb.exe shell /usr/bin/dmesg -c')
	client.close()

def check_program_running(ip, usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR + 'sdb.exe shell sed \'2!d\' /proc/$(pgrep ' + name + ')/status')
	list_out = stdout.readlines()
	input_needed_flag = 0
	for item in list_out:
		if "Sleeping" in item:
			input_needed_flag = 1
	print (input_needed_flag)
	client.close()
	return input_needed_flag

def kill_program(ip, usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR + 'sdb.exe shell pkill ' + name) #$(pgrep ' + name + ')')
	client.close()

def set_root_on(ip, usr, passwd):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR + 'sdb.exe root on')
	client.close()

def list_to_str(lst):
    arg = ""
    for i in range(0, len(lst)):
        arg += lst[i] + " "
    return arg[:-1]

#Send stdin as list and use list_to string for fuzzing stdin as well
def ssh_fuzzing(ip,usr, passwd, program_name, args, stdins, input_size, mode, argv_stdin_pos):
	_args = args[:]
	_stdins = stdins[:]
	stdin_fuzz_string = ""
	fuzz_append_string = "A" * int(input_size)
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	if mode == "argv":
		_args[argv_stdin_pos] += fuzz_append_string
	argv_fuzz_string = list_to_str(_args)
	print(argv_fuzz_string)
	stdin, stdout, stderr = client.exec_command(TOOL_SDB_ADDR + 'sdb.exe shell exec /opt/usr/home/owner/apps_rw/org.example.test001/bin/test001 ' + argv_fuzz_string)
	if mode == "stdin":
		for i in range(0, len(_stdins) + 1):
			if i < len(_stdins):
				stdin_fuzz_string += _stdins[i]
				#stdin_fuzz_string += '\n'
			if i == argv_stdin_pos:
				stdin_fuzz_string += fuzz_append_string
			stdin_fuzz_string += '\n'
		stdin_fuzz_string = stdin_fuzz_string.replace('\r', '')
		print("[+] fuzzing engine... (sending fuzz input)")
		stdin.channel.send(stdin_fuzz_string)
		stdin.channel.shutdown_write()
	client.close()

if __name__ == "__main__":
	if "check_status" in sys.argv[4]:
		check_program_status(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5])
	elif "fuzzing" in sys.argv[4]:
		ssh_fuzzing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
	else:
		print ("[-] Usage: [IP] [USERNAME] [PASSWORD] [FUNCTION]")
