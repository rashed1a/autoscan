import subprocess
import os

print("")
print("Device Information...")
device_data=subprocess.run(['hostnamectl'], capture_output=True, text=True, check=True)
print(device_data.stdout)

print("Updating your device...")
update1 = ['sudo', 'apt-get', 'update']
try:
    update2 = subprocess.run(update1, capture_output=True, text=True, check=True)
    print(update2.stdout)

except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e}")
    print(f"Error output: {e.stderr}")

print("Update Complete...")
cwd = os.getcwd()
print(f"Current directory: {cwd}")
