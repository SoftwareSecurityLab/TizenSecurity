from paramiko import SSHClient
from paramiko import AutoAddPolicy
import sys
def check_program_status(ip,usr, passwd, name):
	#print('aaa')
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command('e:\\iut\\BC_project_symbolic_execution\\Tizen_studio\\tizen-sdk\\tools\\sdb.exe shell tail -n 4  /var/log/dlog/kernel')
	list_out = stdout.readlines()
	#print(list_out)
	status_crash = 0
	for item in list_out:
		if "sig=11" in item and name in item:
			status_crash = 1
	print (status_crash)
	client.close()
	return (status_crash, "SIGSEGV")

def clear_status(ip,usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command('e:\\iut\\BC_project_symbolic_execution\\Tizen_studio\\tizen-sdk\\tools\\sdb.exe shell cp /dev/null /var/log/dlog/kernel')
	client.close()

def check_program_running(ip, usr, passwd, name):
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command('e:\\iut\\BC_project_symbolic_execution\\Tizen_studio\\tizen-sdk\\tools\\sdb.exe shell sed \'2!d\' /proc/$(pgrep ' + name + ')/status')
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
	stdin, stdout, stderr = client.exec_command('e:\\iut\\BC_project_symbolic_execution\\Tizen_studio\\tizen-sdk\\tools\\sdb.exe shell pkill ' + name + ')') #$(pgrep ' + name + ')')
	client.close()
	

#Send stdin as list and use list_to string for fuzzing stdin as well
def ssh_fuzzing(ip,usr, passwd, program_name, args, stdins, input_size):
	print("$$$$$$$$$$$$ $$$$$$$$$$$$$$$$$$$           $$$$$$$$$$$$$$$$$$$$$")
	print(args)
	print(stdins)
	print(input_size)
	stdin_bypass_string = ''
	fuzz_string = ""
	fuzz_append_string = "A" * int(input_size)
	client = SSHClient()
	client.set_missing_host_key_policy(AutoAddPolicy())
	client.connect(ip, username=usr, password=passwd)
	stdin, stdout, stderr = client.exec_command('e:\\iut\\BC_project_symbolic_execution\\Tizen_studio\\tizen-sdk\\tools\\sdb.exe shell exec /opt/usr/home/owner/apps_rw/org.example.test001/bin/test001 ' + args)

	for i in range(0, len(stdins)):
		fuzz_string += stdins[i]
		#fuzz_string += '\n'
	fuzz_string += fuzz_append_string
	fuzz_string = fuzz_string.replace('\r', '')
	print(fuzz_string)
	print("[+] fuzzing engine... (sending fuzz input)")
	stdin.channel.send(fuzz_string + '\n')
	stdin.channel.shutdown_write()
	client.close()

if __name__ == "__main__":
	if "check_status" in sys.argv[4]:
		check_program_status(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5])
	elif "fuzzing" in sys.argv[4]:
		ssh_fuzzing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
	else:
		print ("[-] Usage: [IP] [USERNAME] [PASSWORD] [FUNCTION]")
