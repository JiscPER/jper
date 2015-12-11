# JPER SYSTEM INSTALLATION AND ADMINISTRATION

This document explains how to install JPER, starting from server preparation through to code deployment.

Administering the system is a subset of installation tasks, and depends on choices made during installation, 
hence administration is included in this document also. Ongoing administration tasks that should be done regularly are 
listed specifically in each section and preceded with "ADMIN".

Particularly, if extra resource is required to meet demand, either the machines already running can be scaled up if 
deployed on VM infrastructure taht allows for scaling, or extra server machines should be prepared using these installation 
instructions, and the gateway nginx configuration should be updated to include the new server IP(s) in load balancing pools. 
This is explained in the nginx configuration section of the gateway server installation section below.


## SERVERS

JPER uses a microservice architecture distributed across multiple server machines, in order to allow for easy scaling - 
whichever part of the service needs more performance, just deploy another server and install that part of the service on it. 
The routing of functions to appropriate machines is handled via the web server layer (nginx by default). Configuration of nginx 
is also explained in this document.

Current setup is on amazon virtual machines running ubuntu 14.04 but could run on similar linux systems on other cloud 
hosting providers or other sources of linux hardware. OS installation is not documented here, as it is a matter of following the 
standard instructions for the chosen OS. The software can potentially run on Windows or other OS too, but has not 
been tested and would likely need a few tweaks and entirely different environment configuration which is beyond current scope.

There are five machines deployed in the initial setup:

* gateway - receives and routes requests to the correct machines, and handles secondary tasks like running logging.
* app1 - runs the main JPER app, and has SFTP access configured on it for publisher FTP deposit.
* app2 - runs the supporting apps, the document store, sword-in, sword-out.
* index1 - the elasticsearch index cluster machines.
* index2 - the elasticsearch index cluster machines.

The domain names and current public IP addresses of the machines are listed here for convenience, but of course can change over time:

* pubrouter.jisc.ac.uk router2.mimas.ac.uk 10.0.38.122
* app1.router2.mimas.ac.uk 10.0.94.165
* app2.router2.mimas.ac.uk 10.0.94.164
* index1.router2.mimas.ac.uk 10.0.85.57
* index2.router2.mimas.ac.uk 10.0.85.58

Some useful software should then be installed on all machines, so that python and java are available where required with their 
supporting tools such as virtualenv, gunicorn, pip (the use of these installed tools is covered in this documentation where they 
become necessary):

sudo apt-get install bpython tree nginx git-core htop
sudo apt-get install python-pip python-dev python-setuptools build-essential python-software-properties

sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java7-installer

sudo pip install --upgrade pip
sudo ln -s /usr/local/bin/pip /usr/bin/pip
sudo pip install --upgrade virtualenv
sudo pip install gunicorn
sudo pip install requests


## GATEWAY MACHINE(S)

The main fucntion of the gateway machine is to route and load balance requests to all other machines in the cluster. It can 
also handle secondary tasks such as logging and running the test harness, although this could also be done from any other machine. 

### nginx

CONFIGURE NGINX TO also to answer to gateway:9200 with proxy pass to the upstream index machines
SSL

### logging

setup kibana on router2.mimas.ac.uk

wget https://download.elastic.co/kibana/kibana/kibana-4.0.3-linux-x64.tar.gz
tar -xzvf kibana-4.0.3-linux-x64.tar.gz
rm kibana-4.0.3-linux-x64.tar.gz
mv kibana-4.0.3-linux-x64 kibana4

then to run do the following command (can just go in a screen because logging is not critical to the app)
./kibana4/bin/kibana

and configure nginx to display it

setup logstash server on the gateway router2.mimas.ac.uk (pubrouter.jisc.ac.uk)
https://www.digitalocean.com/community/tutorials/how-to-install-elasticsearch-logstash-and-kibana-4-on-ubuntu-14-04

wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
echo 'deb http://packages.elasticsearch.org/logstash/1.5/debian stable main' | sudo tee /etc/apt/sources.list.d/logstash.list
sudo apt-get update
sudo apt-get install logstash
sudo mkdir -p /etc/pki/tls/certs
sudo mkdir /etc/pki/tls/private

# edit the openssl config and find section v3_ca and add this:
sudo vim /etc/ssl/openssl.cnf
subjectAltName = IP: 10.0.38.122

cd /etc/pki/tls
sudo openssl req -config /etc/ssl/openssl.cnf -x509 -days 3650 -batch -nodes -newkey rsa:2048 -keyout private/logstash-forwarder.key -out certs/logstash-forwarder.crt

# now write the logstash config file:
sudo vim /etc/logstash/conf.d/01-lumberjack-input.conf

input { 
  lumberjack { 
    port => 5000 
    type => "logs" 
    ssl_certificate => "/etc/pki/tls/certs/logstash-forwarder.crt" 
    ssl_key => "/etc/pki/tls/private/logstash-forwarder.key" 
  } 
}

# and configure for syslog
sudo vim /etc/logstash/conf.d/10-syslog.conf

TODO maybe add a match to get multiple item id and type from info, something like (but could be a space in there after the colon):
%{WORD:item_type}:%{WORD:item_id}

filter {
  if [type] == "jperlog" {
    grok {
      patterns_dir => "/etc/logstash/patterns"
      match => { "message" => "%{TIMESTAMP_JPER:timestamp} %{LOGLEVEL:loglevel}: %{WORD:action} - %{DATA:info} \[in %{UNIXPATH:filepath} %{WORD:class} %{WORD:method}\]" }
    }
  }
}

and add a patterns folder and file and put the following content in it:

sudo vim /etc/logstash/conf.d/30-lumberjack-output.conf

output { 
  elasticsearch {
    host => "10.0.85.57"
    cluster => "jper"
  }
  stdout { codec => rubydebug } 
}

The above sets logstash to communicate directly to one of the index machines because it talks on 9300, not on the 9200 that is routed by nginx for the queries
This would cause a problem on machine failure as it does not go through the clustering server setup, but as it is just for logging it is not critical anyway
It does put more indexing load on this machine in the cluster, but that is fine - if the cluster needed more overhead, assigning more machines to it should be 
for the purpose of improving service to end users anyway - not worrying about logging niceties. Unless so much logging happens that it starts to push that one machine over - but that should not happen on this scale
# now restart logstash to make config take effect
sudo service logstash restart


## JPER APPLICATION MACHINE(S)

added supervisord.conf script to jper repo too
https://raw.githubusercontent.com/CottageLabs/sysadmin/master/config/supervisor/supervisord.conf

# get latest version of supervisor via pip
pip install supervisor
curl -s https://raw.githubusercontent.com/Supervisor/initscripts/eb55c1a15d186b6c356ca29b6e08c9de0fe16a7e/ubuntu > ~/supervisord
sudo mv ~/supervisord /etc/init.d/supervisord
sudo chmod a+x /etc/init.d/supervisord
sudo /usr/sbin/service supervisord stop
sudo update-rc.d supervisord defaults
sudo mkdir /var/log/supervisor
sudo mkdir /etc/supervisor/
sudo mkdir /etc/supervisor/conf.d
sudo cp /home/mark/jper/src/jper/supervisord.conf /etc/supervisor/supervisord.conf
sudo ln -s /etc/supervisor/supervisord.conf /etc/supervisord.conf
sudo ln -s /usr/local/bin/supervisord /usr/bin/supervisord
sudo /usr/sbin/service supervisord start
cd /etc/supervisor/conf.d
sudo ln -s /home/mark/jper/src/jper/jper.conf .
sudo supervisorctl reread
sudo supervisorctl update

go into virtualenv of jper and pip install gunicorn

NEED LXML ON JPER APP MACHINE
apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-devc

and make a virtualenv then git clone and submodule init update then pip install -r requirements.txt

added a supervisor file to the jper repo and ln it into the supervisor conf location on app1

added user mark to sudoers for supervisor restart - this was for codeship but seem to have ssh issues there anyway so ignore for now
mark ALL = (root) NOPASSWD:/usr/bin/supervisorctl restart jper

edited /etc/hosts on app1 to route gateway to the current gateway machine at 10.0.38.122
and also routed store to the gateway from the app machine running jper, so that it can find the store at http://store from its store config

### Running the scheduler

Disk location configurations - make sure enough space for ftptmp and tmparchive
Turn off tmparchive when not needed

### Setting up SFTP on a JPER machine

configured app1.router2.mimas.ac.uk to receive sftp requests.
create a group called sftpusers
sudo groupadd sftpusers

created a directory for sftpusers that must be owned by root
sudo mkdir /home/sftpusers

edited the /etc/ssh/sshd_config to put this at the end
commented out the main PasswordAuthentication param so it could be added to the following matches
Match Group !sftpusers
    PasswordAuthentication no
    
Match Group sftpusers
    PasswordAuthentication yes
    ChrootDirectory /home/sftpusers/%u
    AllowTCPForwarding no
    X11Forwarding no
    ForceCommand internal-sftp

then restarted the server to get these changes to take effect.
manually created a test user called testing with password admin, using the commands from the script. Successfully logs in to sftp

need mkpasswd to be installed for the createftpuser.sh so get it along with whois by sudo apt-get install whois

note the changes required via visudo to the createFTPuser.sh and delete scripts, the scripts themselves document the change required


### Setting up log forwarding on the JPER machine(s)

Now setup logstash on app1 to send the jper log to the logstash server running on gateway

First from gateway scp the cert to the app1 machine

scp /etc/pki/tls/certs/logstash-forwarder.crt app1.router2.mimas.ac.uk:/tmp

Then ssh into app1 machine and install logstash client

echo 'deb http://packages.elasticsearch.org/logstashforwarder/debian stable main' | sudo tee /etc/apt/sources.list.d/logstashforwarder.list
wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get update
sudo apt-get install logstash-forwarder
sudo mkdir -p /etc/pki/tls/certs
sudo mv /tmp/logstash-forwarder.crt /etc/pki/tls/certs/
sudo vim /etc/logstash-forwarder.conf

and edit the conf with the following in the network section:

    "servers": [ "10.0.38.122:5000" ],
    "timeout": 15,
    "ssl ca": "/etc/pki/tls/certs/logstash-forwarder.crt"

and this in the files section (top object is just for testing with sys logs, commented out once working):

    {
      "paths": [
        "/var/log/syslog",
        "/var/log/auth.log"
       ],
      "fields": { "type": "syslog" }
    },
    {
      "paths": [
        "/home/mark/jperlog"
       ],
      "fields": { "type": "jperlog" }
    }

then save and close the file and restart logstash forwarder

sudo service logstash-forwarder restart



## STORE APPLICATION MACHINE(S)

clone store and put its supervisor script in place, then run it.

Make sure that the store folder it writes to has plenty disk space (ln to a large disk)

ADMIN - ensure the store app is running. Supervisor brings it up on machine restart, and can be checked with "sudo supervisorctl status"

ADMIN - keep an eye on the disk usage. Expand it when necessary, and/or remove old unnecessary files.


## SWORD-IN / SWORD-OUT APPLICATION MACHINE(S)

Currently same machine as store machine. But does not have to be.

deploying sword-in onto app2
it should not take much resource
and can be deployed on other machines, I will setup a cluster for sword from the gateway to point to it

git clone https://github.com/JiscPER/jper-sword-in.git

follow the install instructions - do lxml
also need to install -e . Simple-sword-server
can also run pip install requirements.txt which does it all

create a local.cfg and put something like this in:
PORT = 5001
JPER_BASE_URL = "https://pubrouter.jisc.ac.uk/api/v1"
JPER_API_KEY = "admin"
SWORD2_SERVER_CONFIG['base_url'] = "https://pubrouter.jisc.ac.uk/sword"

configured the store nginx conf to send /sword to the sword app
also added a sword.conf and gconf.py to the jper-sword-in repo folder (TODO but have not pushed these to the repo yet)
and then:
cd /home/mark/jper-sword-in/src/jper-sword-in
source ../../bin/activate
pip install gunicorn
cd /etc/supervisor/conf.d
sudo ln -s /home/mark/jper-sword-in/src/jper-sword-in/store.conf .
sudo supervisorctl reread
sudo supervisorctl update

NOTE: at this point sword is running but front page throws an error, because the template seems to fail. Should not matter, but get RJ to check


## ELASTICSEARCH INDEX MACHINES

INSTALL ES ON INDEX MACHINES - follow our usual setup.py instructions and then configure as per infrastructure for specific sync by IP 
and install plugins
bin/plugin -install mobz/elasticsearch-head
bin/plugin install elasticsearch/elasticsearch-mapper-attachments/2.4.3

installed on index1 then tarred the whole dir and copied to index2
and put the forwarder to the init script in place
and installed java again



