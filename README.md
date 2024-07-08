# autoscan
AutoScan is a Linux-based vulnerability assessment tool that develops and scans websites using bash scripting. This tool can help you scan a website for reconnaissance / information gathering and vulnerability assessment. When a security researcher tries to collect information from a website, the full process takes a lot of time and is a hassle. To solve the problem and reduce the time problem, I developed this tool. AutoScan is capable of gathering reconnaissance / information gathering and vulnerability assessment tool on a single platform and making a scan process that reduces the extra time consumed. Also, using this tool users can create a real-time VA report for the target website and share it in text format. Every automatic scanning tool has the big issue that there is just some control that makes some time problematic for a researcher. And it can’t take manual control, but this tool gives the user manual control to configure their assessment strategy. Users can use this tool to scan individual WordPress CMSs for vulnerability assessment. The main purpose of developing this tool is to increase the user's work process and reduce extra time spent on cyber security research.

You can also find me on my website, https://balagos.com/

To use this tool, you need to run some commands first;

=> sudo git clone https://github.com/rashed1a/autoscan.git

=> cd autoscan

=> sudo chmod +x autoscan.sh

=> python update_os.py  [To avoid backdated resource-related issues.]

=> python system_upgrade.py   [Note: Only run system_upgrade.py if you want to upgrade your system; otherwise, there is no need to run system_upgrade.py because this process takes a long time to complete.]

=> ./autoscan.sh
