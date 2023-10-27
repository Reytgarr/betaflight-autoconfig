import serial.tools.list_ports
import datetime
import os
import git

repo_path = "f:/quad/!config"

if not os.path.exists(repo_path):
    git.Repo.clone_from("https://github.com/Reytgarr/betaflight-config.git", repo_path)

repo = git.Repo(repo_path)
origin = repo.remote(name='origin')
origin.pull()

ports = serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    com_port = port

baud_rate = 115200
ser = serial.Serial(port=com_port, baudrate=baud_rate, timeout=1)

command = "#\n"
ser.write(command.encode('utf-8'))
response = ser.readlines()


command = "diff all\n"
ser.write(command.encode('utf-8'))
response = ser.readlines()
response_str = ''.join(map(lambda x: x.decode('utf-8'), response))
print(response_str)

name_line = [line for line in response_str.split('\n') if 'board_name' in line]
if name_line:
    name = name_line[0].split('board_name')[1].strip()
    
    board_name = name
else:
    board_name = ''


for line in response_str.split('\n'):

    if "Betaflight /" in line and "(" in line and ")" in line:
        version_start = line.index(")") + 2
        version_end = line.index(" ", version_start)
        version = line[version_start:version_end]
        break

file_path = f"{repo_path}/{board_name}_{version}.txt"  
temp_path = f"{repo_path}/{board_name}_{version}_temp.txt"  


with open(temp_path, "w") as file:
    file.write(response_str)
ser.close()

if not os.path.exists(file_path):
    with open(file_path, "w") as file:
        file.write(response_str)
        ser.close()
else:
    with open(file_path, 'r') as file1, open(temp_path, 'r') as file2:
        if file1.read() == file2.read():
            print("The files are the same")
        else:
            with open(file_path, "w") as file:
                file.write(response_str)
                ser.close()
        
os.remove(temp_path)
repo = git.Repo(repo_path)
repo.git.add(file_path)
repo.index.commit("Added new config file")
origin = repo.remote(name='origin')
origin.push()
