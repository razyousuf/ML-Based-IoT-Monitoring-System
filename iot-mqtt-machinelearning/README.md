# README #

This README file contains the setup process for an IoT API ML model setup.
This shows how to connect IoT devices to Machine Learning Models.

Please see the IoT-MasterClass Youtube page for installation help.
https://www.youtube.com/@codewithfrancis

This service collects sensor data from IoT devices and makes predictions using a RandomForestClassifier Model.

### Reguirements

* Install a source-code editor like Visual Studio Code
  * https://code.visualstudio.com/download
* Install PYTHON 3+

### Setup Using Linode Server (Youtube Video Example)
* Linode has some free options, so happy coding.
* Create a Linode (https://www.linode.com/) account
* Linode Setup:
  * Create a Linux Server
    * Choose Ubuntu 22.04 LTS image
    * Select a Region
    * Select a plan. (Shared plans are cheaper)
    * Add Label Name and tags
    * Add a Root password
    * Add an SSH Key:
      * Generate SSH key on your computer with command: 
        * ssh-keygen -t ed25519 -C "user@domain.tld"
          * see example at: https://www.linode.com/docs/guides/use-public-key-authentication-with-ssh/?tabs=ed25519-recommended,manually,ssh-add
        * get the sshkey location.
        * copy and paste the pub key file text contents into the linode server
    * Click Create Linode (wait for provisioning and boot)
  * After Linode server is started, you can launch it using the LISH Web Console or an SSH Client
  
* Login with LISH Console:
  * user: root
  * pswd: created root password from above
  
* Login with visual studio
  * Open visual studio
  * Install Extension: 'Remote Development'
  * After extension is installed 
    * click on the '><' icon on the bottom left of the screen,
    * or go to Remote Explorer
    * select connect current window to host
    * click: 'Configure SSH host'
    * click: the location of your ssh key created for the server above.
    * add host connection parameters:
      * Host any-name-for-my-linode-server
	    * HostName 100.100.100.100 --> server IP address
	    * User root
	    * IdentityFile /Users/my-folder/.ssh/ssh_file_name --> Location to my SSH file
      * For more info, see : https://code.visualstudio.com/docs/remote/ssh
    * Now you can connect with SSH:
      * click on the '><' icon on the bottom left of the screen,
      * or go to Remote Explorer
      * select connect current window to host
    
  
* Install ML Dependencies
  * Install pip for python
    * apt install pip
    * OR: apt install python3-pip
  * pip install gekko
  * pip install matplotlib
  * pip install pandas
  * pip install scikit-learn==1.2.2
  * pip install joblib==1.3.2

* Install FastApi Dependencies
  * pip install fastapi[all]
    * This command above Instals:
      * pip install fastapi
      * pip install "uvicorn[standard]"
      
* Install Code Dependencies
  * pip install paho-mqtt
  
* API Code Installation
  * Download this repo and copy it ito your root folder
  * Run Code using
    * uvicorn main:app --reload



### Setup file
* In app_constants.py configure your:
  * USERNAME = "mqtt_user_name"
  * PASSWORD = "mqtt_password"
  * MASTER_CONTROL_TOPIC = "iot/control"
  * MASTER_TELEMETRY_TOPIC = "iot/telemetry"
  * SERVER_URL = "mqtt_server_url"
* Download this repo and copy it ito your root folder
* Run Code using
  * uvicorn main:app --reload
* open swagger: 127.0.0.1:8000/docs#/


### License

* MIT License
* Free to copy, share, modify and use as needed.
* Happy coding!