import serial.tools.list_ports
import datetime
import os
import git
import time
from dotenv import load_dotenv
import pystray
from PIL import Image
import threading

load_dotenv()

repo_path = os.getenv("REPO_PATH")
repo_url = os.getenv("REPO_URL")
baud_rate = os.getenv("BAUD_RATE")

if not os.path.exists(repo_path):
    git.Repo.clone_from(repo_url, repo_path)

def on_exit(icon, item):
    icon.stop()

def create_tray_icon():
    image = Image.open("bf_icon.ico")
    menu = pystray.Menu(pystray.MenuItem("Exit", on_exit))
    icon = pystray.Icon("Betaflight Autoconfig", image, "Betaflight Autoconfig", menu)
    return icon

def port_monitor():
    while True:
        ports = serial.tools.list_ports.comports()
        previous_ports = [port.device for port in ports]
        time.sleep(1)
        ports = serial.tools.list_ports.comports()
        current_ports = [port.device for port in ports]

        new_ports = set(current_ports) - set(previous_ports)

        for new_port in new_ports:
            ser = serial.Serial(port=new_port, baudrate=baud_rate, timeout=1)

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
            else:
                with open(file_path, 'r') as file1, open(temp_path, 'r') as file2:
                    if file1.read() == file2.read():
                        print("The files are the same")
                    else:
                        with open(file_path, "w") as file:
                            file.write(response_str)

            os.remove(temp_path)
            repo = git.Repo(repo_path)
            repo.git.add(file_path)
            repo.index.commit("Added new config file")
            origin = repo.remote(name='origin')
            origin.push()

def main():
    icon = create_tray_icon()

    def main_thread():
        icon.run()
    
    port_thread = threading.Thread(target=port_monitor)
    port_thread.daemon = True
    port_thread.start()
    
    main_thread()

if __name__ == '__main__':
    main()
