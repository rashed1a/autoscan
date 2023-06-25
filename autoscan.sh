#! /bin/bash
sudo apt-get install lolcat -y > additional_file.txt
echo "############################################################" | lolcat 
echo "#    _   _   _ _____ ___  ____   ____    _    _   _        #
#     / \ | | | |_   _/ _ \/ ___| / ___|  / \  | \ | |     #
#    / _ \| | | | | || | | \___ \| |     / _ \ |  \| |     #
#   / ___ \ |_| | | || |_| |___) | |___ / ___ \| |\  |     #
#  /_/   \_\___/  |_| \___/|____/ \____/_/   \_\_| \_|     #
#                                                          #
#     autoscan developed for kali linux distribution.      #
#     autoscan is a automated web scanning tool that       #
#     gives you information and vulnerability report       #
#                   from target website.                   #
#            https://rashedsworld.com/index.html           #
#                                                          #" | lolcat
echo "############################################################" | lolcat
echo ""
printf "==>Enter website url with www and without http:// or https:// (www.example.com): " & read url

mkdcd1 ()
{
	mkdir $url
	cd $url
        mkdir Reconnaissance
        touch Install.txt
        touch info.txt
}

mkdcd2 ()
{
	mkdir $url
	cd $url
        mkdir Vulnerability_Assessment
        touch Install.txt
        touch info.txt
}

mkdcd3 ()
{
	mkdir $url
	cd $url
        mkdir Reconnaissance
        mkdir Vulnerability_Assessment
        touch Install.txt
        touch info.txt
}

mkfR ()
{
	touch dns_scan.txt
	touch load_balancer_check.txt
	touch firewall_check.txt
	touch network_scan.txt
	touch sslcan.txt
}

mkfva ()
{
	touch network_assessment.txt
	touch Vulnerability_scan.txt
	touch wordpress_scan.txt
	touch url_brute_force_scan.txt
}

inst ()
{
	echo ""
	echo "####################################"
	echo "#                                  #"
	echo "#     INSTALLATION PROCESS         #"
	echo "#                                  #"
	echo "####################################"
	echo ""
	echo "=>Starting dependency installation..."    
	sudo apt-get install fierce -y > Install.txt
	echo "" >> Install.txt
	sudo apt-get install lbd -y >> Install.txt
	echo "" >> Install.txt
	sudo apt-get install wafw00f -y >> Install.txt
	echo "" >> Install.txt
    	sudo apt-get install sslscan -y >> Install.txt
    	echo "" >> Install.txt
    	sudo apt-get install nikto -y >> Install.txt
    	echo "" >> Install.txt
    	sudo apt-get install dirb -y >> Install.txt
    	echo "" >> Install.txt
	echo "autoscan developed for Information Gathering and Vulnerability Assessment." > info.txt
        sudo apt-get install dnsenum -y >> Install.txt
        echo "" >> Install.txt
	sudo apt-get install dnsrecon -y >> Install.txt
        echo "" >> Install.txt
	echo "=>Sependency installation finished"
        echo "-------------------------------------"

}

rscan ()
{
	echo ""
	echo "####################################"
	echo "#                                  #"
	echo "#     INFORMATION GATHERING        #"
	echo "#                                  #"
	echo "####################################"
	echo ""
	echo "Information gathering for "$url""  
	echo "=>DNS scanning..."
	fierce --domain "$url" > dns_scan.txt
	echo "" >> dns_scan.txt
	echo "" >> dns_scan.txt
	dnsenum "$url" >> dns_scan.txt
	echo "" >> dns_scan.txt
        echo "" >> dns_scan.txt
	dnsrecon -d "$url" >> dns_scan.txt
	echo "DNS scanning done"
	echo "=>Network scanning ..."
	nmap -sV "$url" > network_scan.txt
	echo "Network scanning done"
	echo "=>Ssl service scaning ..."
	sslscan "$url" > sslcan.txt
	echo "Ssl service scaning done"
	echo "=>Scanning for load balencer check..."
	lbd "$url" > load_balancer_check.txt
	echo "Load balencer checking done" 
	echo "=>Scanning for Firewall check..."
	wafw00f "$url" > firewall_check.txt
	echo "Firewall checking done"
	echo "-------------------------------------"
}

rscan1 ()
{
	echo ""
	echo "####################################"
	echo "#                                  #"
	echo "#     INFORMATION GATHERING        #"
	echo "#                                  #"
	echo "####################################"
	echo ""
	echo "Information gathering for "$url""  
	echo "======== DNS scanning ========..."
	#fierce --domain "$url"
	echo "" >> dns_scan.txt
	echo "" >> dns_scan.txt
	dnsenum --noreverse "$url"
	echo "" >> dns_scan.txt
        echo "" >> dns_scan.txt
	dnsrecon -d "$url"
	echo "======== DNS scanning done ========"
	echo "||"
	echo "======== Network scanning ========"
	nmap -sV "$url"
	echo "======== Network scanning done ========"
	echo "||"
	echo "======== Ssl service scaning ========"
	sslscan "$url"
	echo "======== Ssl service scaning done ========"
	echo "||"
	echo "======== Scanning for load balencer check ========"
	lbd "$url"
	echo "======== Load balencer checking done ========" 
	echo "||"
	echo "======== Scanning for Firewall check ========"
	wafw00f "$url"
	echo "======== Firewall checking done ========"
	echo "-------------------------------------"
}

vascan ()
{
	echo ""
	echo "######################################"
	echo "#                                    #"
	echo "#     VULNERABILITY ASSESSMENT       #"
	echo "#                                    #"
	echo "######################################"
	echo ""
	echo "Vulnerability Assessment for "$url""
	echo "=>Network Assessment running ..."
	nmap --script vuln -sV "$url" > network_assessment.txt
	echo "Network Assessment done"
	echo "=>Vulnerability Assessment running..."
	nikto -host "$url" > Vulnerability_scan.txt
	echo "Vulnerability Assessment done"
	echo "=>Wordpress vulnerability scanning ..."
	wpscan --url "$url" > wordpress_scan.txt
	echo "Wordpress vulnerability scanning done"
	uba

}

uba ()
{
	echo "Do you want url brute-force attack for "$url"? (Y/N)"
	read input
	a=y
	b=Y
	c=n
	d=N
	if [ $input == $a -o $input == $b ]
	then
	echo "=>Url brute-force attack start..."
	dirb https://"$url" > url_brute_force_scan.txt
	echo "Url brute-force attack done"
	elif [ $input == $c -o $input == $d ]
	then
	echo "url brute-force attack for "$url" rejected"
	echo "url brute-force attack for "$url" rejected" > url_brute_force_scan.txt
	else
	echo "url brute-force attack for "$url" rejected"
	echo "url brute-force attack for "$url" rejected" > url_brute_force_scan.txt
	fi
}

vascan1 ()
{
	echo ""
	echo "######################################"
	echo "#                                    #"
	echo "#     VULNERABILITY ASSESSMENT       #"
	echo "#                                    #"
	echo "######################################"
	echo ""
	echo "Vulnerability Assessment for "$url""
	echo "======== Network Assessment running ========"
	nmap --script vuln -sV "$url"
	echo "======== Network Assessment done ========"
	echo "||"
	echo "======== Vulnerability Assessment running ========"
	nikto -host "$url"
	echo "======== Vulnerability Assessment done ========"
	echo "||"
	echo "======== Wordpress vulnerability scanning ========"
	wpscan --url "$url"
	echo "======== Wordpress vulnerability scanning done ========"
	uba

}

uba1 ()
{
	echo "Do you want url brute-force attack for "$url"? (Y/N)"
	read input
	a=y
	b=Y
	c=n
	d=N
	if [ $input == $a -o $input == $b ]
	then
	echo "======== Url brute-force attack start ========"
	dirb https://"$url" > url_brute_force_scan.txt
	echo "======== Url brute-force attack done ========"
	elif [ $input == $c -o $input == $d ]
	then
	echo "url brute-force attack for "$url" rejected"
	else
	echo "url brute-force attack for "$url" rejected"
	fi
}

inf ()
{
	
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   Reconnaissance / Information gathering"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time     :   "   & date
	echo "---------------------------------------------------------------"
}

menu ()
{
	echo ""
	echo "Select your sanning section:"
	echo ""
	echo "1) Reconnaissance / Information gathering without report"
	echo "2) Reconnaissance / Information gathering with report"
	echo ""
	echo "3) Vulnerability Assessment without report"
	echo "4) Vulnerability Assessment with report"
	echo ""
	echo "5) Reconnaissance and Vulnerability Assessment without report"
	echo "6) Reconnaissance and Vulnerability Assessment with report"
	echo ""
	printf "Please select (1/2/3/4/5/6): " & read a
	x="Reconnaissance / Information gathering without report"
	y="Reconnaissance / Information gathering with report"
	z="Vulnerability Assessment without report"
	xx="Vulnerability Assessment with report"
	yy="Reconnaissance and Vulnerability Assessment without report"
	zz="Reconnaissance and Vulnerability Assessment with report"
	if [ $a == 1 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $x"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time     :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd1
	inst
	rscan1
	echo "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	elif [ $a == 2 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $x"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time     :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd1
	inst
	cd Reconnaissance
	mkfR
	rscan
	echo "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	echo "Your scanning report path: "
	pwd
	elif [ $a == 3 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $x"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time     :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd2
	inst
	vascan1
	echo "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	elif [ $a == 4 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $x"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time     :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd2
	inst
	cd Vulnerability_Assessment
	mkfva
	vascan
	echo "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	echo "Your scanning report path: "
	pwd
	elif [ $a == 5 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $z"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time   :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd3
	inst
	rscan1
	vascan1
	printf "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	elif [ $a == 6 ]
	then
	echo ""
	echo "---------------------------------------------------------------"
	echo "=>Target Url     :   $url"
	echo "=>Target Section :   $z"
	echo "=>Scan Type      :   Full scan"
	printf "=>Start Time   :   "   & date
	echo "---------------------------------------------------------------"
	mkdcd3
	inst
	cd Reconnaissance
	mkfva
	rscan
	cd ..
	cd Vulnerability_Assessment
	mkfva
	vascan
	cd ..
	printf "ThakYou for Using AutoScan in Your Work Station" | lolcat -i
	echo "Your scanning report path: "
	pwd
	else
	echo ""
	menu
	fi
}
menu