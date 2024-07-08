# autoscan
AutoScan is a Linux based vulnerability assessment tools that develop for scan website using 
bash scripting. This tool can help you to scan website for Reconnaissance / Information 
gathering and Vulnerability Assessment. When a security researcher tries to collect information 
from a website, the full process takes loot of time and makes hassle. To solve the problem and 
reduce the time problem I develop this tool. AutoScan capable to gather Reconnaissance / 
Information gathering and Vulnerability Assessment tool in a single platform and make a scan 
process that reduces the extra time consuming. Also using this tool user can create a real time 
VA report for the target website and share as a text format. Every automatic scanning tool has 
a big issue that there is just some of control that make problematic some time for a researcher 
and can’t take manual control but this tool gives user manual control to configure their 
assessment strategi. User can use this tool to scan individual WordPress CMS for vulnerability 
assessment. The main purpose of develop this tool is to increases user work process and reduce 
extra time consuming in cyber security research.
You also find me in my website https://rashedsworld.com/

For using this tool you need to run some command 1st

=> sudo git clone https://github.com/rashed1a/autoscan.git

=> cd autoscan

=> sudo chmod +x autoscan.sh

Note: It will update your system to avoid backdated resource-related issues.

=> python update_os.py

Note: Only run upgrade_os.py if your machine is not upgraded; otherwise, there is no need to run upgrade_os.py because this process takes a long time to complete.

=> python upgrade_os.py

=> ./autoscan.sh
