# JPER SYSTEM INSTALLATION AND ADMINISTRATION

This document explains how to install JPER, starting from server preparation through to code deployment.

Administering the system is a subset of installation tasks, and depends on choices made during installation, 
hence administration is included in this document also. Ongoing administration tasks that should be done regularly are 
listed specifically in each section and preceded with "ADMIN".

Particularly, if extra resource is required to meet demand, either the machines already running can be scaled up if 
deployed on VM infrastructure that allows for scaling, or extra server machines should be prepared using these installation 
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
* app2 - runs the supporting apps, the document store, sword-in, sword-out, oai-pmh.
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

Finally, there are useful scripts in the jper code repository in which this document is originally located,so clone the git repo onto the machines.
At time of writing these documents, which at said time are available in the repo itself, the repo can be retrieved into your user directory - and into 
a virtualenv just to keep it neat if running it - as such:

    cd ~
    virtualenv -p python2.7 jper --no-site-packages
    cd jper
    mkdir src
    cd src
    git clone http://github.com/jiscper/jper

(some of the following installation/configuration/administration may assume that things are in the home directory of the user account that 
originally configured the system, which was called "mark". If desired, all such commands could be substituted with a different username.)


## GATEWAY MACHINE

The main fucntion of the gateway machine is to route and load balance requests to all other machines in the cluster. It can 
also handle secondary tasks such as logging and running the test harness, although this could also be done from any other machine. 


### nginx

nginx is already installed on the gateway server, if following this documenation so far. If not, just "sudo apt-get install nginx". Then, copy 
(or symlink) the file from the jper repo (which should also already be on the server, otherwise see above) into the sites-enabled directory of 
nginx and then restart it to get it going

    cd /etc/nginx/sites-enabled
    sudo ln -s ~/jper/src/jper/deployment/jper_nginx .

    sudo /etc/init.d/nginx restart

ADMIN: it is necessary to configure nginx to serve the /admin route of jper to ONLY the first jper machine, where the sftp user accounts are 
capable of being created, otherwise user accounts for publishers may fail to create sftp accounts if the requests go to the wrong machine. 
At the moment this does not matter because only one machine is running JPER, but if it has to be scaled up this must be taken into account. 
So don't send the /admin route to the processing pool but direct to the first machine, if scaling is done in futre.


### logging

Logging is handled by the jper app itself, and it is configured to write to a file called "logfile". However, logstash and kibana have also 
been installed to allow easier exploration of logs. This need not run at all times, but can be useful. This need not be on the gateway machine, 
but for now it is.

First, get the kibana software:

    wget https://download.elastic.co/kibana/kibana/kibana-4.0.3-linux-x64.tar.gz
    tar -xzvf kibana-4.0.3-linux-x64.tar.gz
    rm kibana-4.0.3-linux-x64.tar.gz
    mv kibana-4.0.3-linux-x64 kibana4

And it is simple to run, with the following command:

    ./kibana4/bin/kibana

This could also be run using supervisor, but as kibana is not critical to the running of the app, supervisor has not been configured for it. 
Instead, to leave it running long term, just use the "screen" command to start a new terminal screen and run the above command there.

The nignx configuration already installed will by default serve kibana from the gateway server.

In order to feed kibana with useful information from the logs, the logstash server must also be installed. There are useful instructions here:

https://www.digitalocean.com/community/tutorials/how-to-install-elasticsearch-logstash-and-kibana-4-on-ubuntu-14-04

And the commands actually used to install it are as follows:

    wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
    echo 'deb http://packages.elasticsearch.org/logstash/1.5/debian stable main' | sudo tee /etc/apt/sources.list.d/logstash.list
    sudo apt-get update
    sudo apt-get install logstash
    sudo mkdir -p /etc/pki/tls/certs
    sudo mkdir /etc/pki/tls/private

Then open the openssl config file for editing

    sudo vim /etc/ssl/openssl.cnf

And find section v3_ca and add the following:

    subjectAltName = IP: 10.0.38.122

Then save and close the file.

(NOTE: the IP above is correct at time of writing these documents - but check for later installs.)

Now run openssl to make a key

    cd /etc/pki/tls
    sudo openssl req -config /etc/ssl/openssl.cnf -x509 -days 3650 -batch -nodes -newkey rsa:2048 -keyout private/logstash-forwarder.key -out certs/logstash-forwarder.crt

Now write the logstash config file:

    sudo vim /etc/logstash/conf.d/01-lumberjack-input.conf

And put this in it

    input { 
      lumberjack { 
        port => 5000 
        type => "logs" 
        ssl_certificate => "/etc/pki/tls/certs/logstash-forwarder.crt" 
        ssl_key => "/etc/pki/tls/private/logstash-forwarder.key" 
      } 
    }

And now write the syslog config file:

    sudo vim /etc/logstash/conf.d/10-syslog.conf

And put this in it:

    %{WORD:item_type}:%{WORD:item_id}

    filter {
      if [type] == "jperlog" {
        grok {
          patterns_dir => "/etc/logstash/patterns"
          match => { "message" => "%{TIMESTAMP_JPER:timestamp} %{LOGLEVEL:loglevel}: %{WORD:action} - %{DATA:info} \[in %{UNIXPATH:filepath} %{WORD:class} %{WORD:method}\]" }
        }
      }
    }

Then add a patterns folder and file and put the following content in it:

    sudo vim /etc/logstash/conf.d/30-lumberjack-output.conf

    output { 
      elasticsearch {
        host => "10.0.85.57"
        cluster => "jper"
      }
      stdout { codec => rubydebug } 
    }

ADMIN: note that the logstash configs depend on the structure of the data being sent to them. The above was correct at time of writing, but 
check the configuration files on the running machines for latest versions. If in future the data strucrtures are altered, check the logstash 
configs can still handle the incoming data as expected.

NOTE: The above sets logstash to communicate directly to one of the index machines because it talks on 9300, not on the 9200 that is routed by nginx for the queries
This would cause a problem on machine failure as it does not go through the clustering server setup, but as it is just for logging it is not critical anyway
It does put more indexing load on this machine in the cluster, but that is fine - if the cluster needed more overhead, assigning more machines to it should be 
for the purpose of improving service to end users anyway - not worrying about logging niceties. Unless so much logging happens that it starts to push that one machine over - but that should not happen on this scale

Now restart logstash to make the configs take effect

    sudo service logstash restart

ADMIN: Logstash will create daily indexes in the elasticsearch cluster. Once they are of no further use, they should be deleted.
Otherwise the cluster will get far larger than necessary.

The command to delete an index is:

    curl -X DELETE http://gateway:9200/logstash-<FULL_NAME_OF_INDEX_YOU_WANT_TO_REMOVE>

Of course, BE CAREFUL WITH DELETE COMMANDS.

See the elasticsearch documentation for more information.


## JPER APPLICATION MACHINE(S)

Firstly, install supervisor which keeps apps up and running. There are configurations in the jper repo, which can be copied into place 
as demonstrated below along with the install commands:

    pip install supervisor
    curl -s https://raw.githubusercontent.com/Supervisor/initscripts/eb55c1a15d186b6c356ca29b6e08c9de0fe16a7e/ubuntu > ~/supervisord
    sudo mv ~/supervisord /etc/init.d/supervisord
    sudo chmod a+x /etc/init.d/supervisord
    sudo /usr/sbin/service supervisord stop
    sudo update-rc.d supervisord defaults
    sudo mkdir /var/log/supervisor
    sudo mkdir /etc/supervisor/
    sudo mkdir /etc/supervisor/conf.d
    sudo cp /home/mark/jper/src/jper/deployment/supervisord.conf /etc/supervisor/supervisord.conf
    sudo ln -s /etc/supervisor/supervisord.conf /etc/supervisord.conf
    sudo ln -s /usr/local/bin/supervisord /usr/bin/supervisord
    sudo /usr/sbin/service supervisord start
    cd /etc/supervisor/conf.d
    sudo ln -s /home/mark/jper/src/jper/deployment/jper.conf .
    sudo supervisorctl reread
    sudo supervisorctl update

Now start up the virtualenv for the jper software and install gunicorn

    cd ~/jper/src/jper
    source ../../bin/activate
    pip install gunicorn

And lxml is also needed on the jper app machine, so run these commands to install it:

    sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-devc

mkpasswd is also required by user management scripts in the jper codebase, so run the following command to install it on the machine:

    sudo apt-get install whois

To actually use the jper software, we must also install it. Check the README from the repo for software install instructions, but 
it should conform to the following:

    cd ~/jper/src/jper
    source ../../bin/activate
    git submodule init
    git submodule update
    pip install -r requirements.txt

ADMIN: superuser permissions must be given to the user that will be running the code, to run the scripts to create, delete users, and move user files.
This only needs to happen on the first jper machine, as it is assumed to coincide with the machine where sftp access is also configured.
The changes required via visudo so that the createFTPuser.sh, deleteFTPuser.sh and moveFTPfiles.sh (which can be found in the service/models directory) 
are documented in the scripts themselves - see them for further information.

Necessary settings for JPER are in config/service.py. However, to change them it is best to use a local.cfg in the top level directory of the application. 
In there, any setting found in config/service.py can be overwritten and it will be read by the running service.

Now, configure the hosts on the machine so that requests to the gateway machine go to the correct place (IP correct at time of writing this document)
Also, put in a route for the server that will be running the document store software too, so that it can be found by the software.

    sudo vim /etc/hosts

ADMIN: The routes to the gateway and to the store will depend on the IP addresses of the VMs being used in the cluster. 
Lookup the hosts file on the running VM to find the current routes to gateway and store.

When ready, the app can be started as follows:

    sudo supervisorctl start jper

Stopping and status can be performed as expected, with the following commands, when necessary:

    sudo supervisorctl stop jper
    sudo supervisorctl restart jper
    sudo supervisorctl status

ADMIN: check that the jper app is always running, eitehr manually with the supervisor command, or by installing your preferred application 
monitoring and alerting tools.


### Running the jper app scheduler

The jper app includes a scheduler, which in simple configuration can be run by the app itself. This however requires restricting the app to 
one worker and one thread. So in production, the app runs on multiple workers (via the supervisor config) and multithreaded (via the app config).
So the scheduler, which must run to check the SFTP deposits by publishers, and to check unrouted notifications and route them to matched institutions, 
shoud be started separately.

ADMIN: The scheduler is controlled by config options on the config/service.py file. Be sure to set RUN_SCHEDULE to False in production, 
and to set the processing times for the processes that should run, and to choose whether or not routed and unrouted notifications should be deleted.

ADMIN: Ensure there is sufficient disk space for the locations configured for the sftpusers directories and the ftp tmp directories. Note that 
JPER was NOT specified or designed to act as a long term store - the content is only held for testing, and should really be removed after processing. 
The "store" module does store items longer term, so that they can be retrieved by repositories. However even this was intended only to last up to 
three months - so keep an eye on disk space.

ADMIN: At present there is also a tmp archive in use, keeping an exact copy of everything received via ftp from any publishers. This was to 
ensure we could test received content and know exactly how it arrived. This will take up extra space on disk though, and so can be disabled 
when no longer deemed necessary. To disable this, see the service/models.moveFTPfiles.sh script, and comment out the two lines that create and move to tmparchive.

Running the scheduler is straightforward. Start a new terminal screen and enter the following command:

    screen
    cd ~/jper/src/jper
    source ../../bin/activate
    python service/scheduler.py

To kill the scheduler, if ctrl-c in the screen window fails, find the pid of the running process and kill it:

    ps -ef | grep scheduler
    kill -9 &lt;pid&gt;

ADMIN: There is also a scheduler supervisor configuration in the deployment folder, although this has NOT yet been set up. To do so, symlink it 
into the supervisor configs directory as per supervisor instructions above. This would ensure the scheduler runs if the machine reboots, 
but for now this has been kept manual as it is the direct way to ensure incoming files from publishers are processed at a time when we 
can check on the processing - of course, longer term, you would not want to do this manually all the time, but when bringing on new publishers 
it is useful to have direct control.

NOTE: the scheduler scripts make some assumptions about how the SFTP accounts are configured and used by publishers. In particular, 
the scheduler will expect them to be on the same machine, and in a certain location. See below for configuring SFTP, and keep this in 
mind when scaling up - whilst the jper app code can be easily scaled to run the service on multiple machines, the scheduler will need to 
be only on the machine that has the sftp accesses configured. Whilst other scheduled operations could run on mutliple machines, there is no 
handling in place to ensure notifications do not then end up being processed on multiple machines - so, keep the scheduler running only on 
one machine. When the scheduler processes notifications, those would be POSTed into the pool of machines running the app anyway, so the actual 
work of dealing with them after they are processed out of the SFTP directories will be spread across the pool.

ADMIN: check regularly that the scheduler is running, or no incoming notifications will be processed (although they also will not be lost). 
This can be monitored using your preferred app monitoring tools, or manually.

ADMIN: check that any local copies of processed files being held in ftptmp are being removed - they should only be there temporarily during processing.
Also, any files in the sftpusers directories should be getting processed and removed if the scheduler is running properly, so check there too.

ADMIN: if the tmparchive option is being used to make sure an exact copy of files as recevied from publishers is being kept, keep an eye on how much 
storage is being used.


### Setting up SFTP on a JPER app machine

SFTP is configured on the first jper app machine, to ensure secure access for publishers to deposit articles via FTP. The publisher accounts 
are created and managed via the jper software, so the machine just needs to be configured to give those user accounts SFTP rights.

First, create a group called sftpusers

    sudo groupadd sftpusers

Then created a directory for sftpusers that must be owned by root

    sudo mkdir /home/sftpusers

Edit the /etc/ssh/sshd_config

    sudo vim /etc/ssh/sshd_config

Comment out the default PasswordAuthentication parameter in the file, then put this at the end:

    Match Group !sftpusers
        PasswordAuthentication no

    Match Group sftpusers
        PasswordAuthentication yes
        ChrootDirectory /home/sftpusers/%u
        AllowTCPForwarding no
        X11Forwarding no
        ForceCommand internal-sftp

Then restart the server to get these changes to take effect.


### Setting up log forwarding on the JPER app machine(s)

Now setup logstash on app1 to send the jper log to the logstash server running on gateway

First, login (ssh) to the gateway machine where the logstash server was installed (or whichever machine it was installed to) and copy the 
certificate that was generated previously onto the app machine, for example with the below command:

    scp /etc/pki/tls/certs/logstash-forwarder.crt app1.router2.mimas.ac.uk:/tmp

Then login (ssh) to the app machine and install logstash client

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

then save and close the file and restart logstash forwarder:

    sudo service logstash-forwarder restart

Repeat this process on any machine that you want to submit logs to the logstash server.

NOTE: the IPs and logfile names shown in the above configs are correct at time of writing this documentation. However, 
of course, they can be augmented as necessary to suit any future installations.


## STORE APPLICATION MACHINE

Login (ssh) to the machine on which the store is to be installed, and perform the following:

    cd ~
    virtualenv -p python2.7 store --no-site-packages
    cd store
    mkdir src
    cd src
    git clone https://github.com/JiscPER/store.git
    cd store
    source ../../bin/activate
    pip install -e .
    pip install gunicorn

There is a file called "storage" in the code repo, which provides an nginx configuration for connection to the store. This should be copied or 
symlinked into the nginx sites-enabled folder, and then nginx should be restarted:

    cd /etc/nginx/sites-enabled
    sudo ln -s ~/store/src/store/deployment/storage .
    sudo /etc/init.d/nginx restart
    
There is also a supervisor config file for the store, called "store.conf". Put it in place too:

    cd /etc/supervisor/conf.d
    sudo ln -s ~/sword/src/sword/deployment/store.conf .
    sudo supervisorctl reread
    sudo supervisorctl update

NOTE: Make sure that the store folder it writes to has plenty disk space. Configuring some warnings on the system or using a monitoring service 
would be a good idea.

ADMIN - ensure the store app is running at all times. Supervisor brings it up on machine restart, and can be checked with "sudo supervisorctl status"

ADMIN - keep an eye on the disk usage. Expand it when necessary, and/or remove old unnecessary files.


## SWORD-IN / SWORD-OUT / OAIPMH APPLICATION MACHINE


SWORD-IN

The initial installation placed the sword-in and sword-out and oaipmh software on the same machine as the store software, but they do not have to be on the same machine.

Login (ssh) to the machine on which sword is to be installed, and perform the following:

    cd ~
    virtualenv -p python2.7 jper-sword-in --no-site-packages
    cd jper-sword-in
    mkdir src
    cd src
    git clone https://github.com/JiscPER/jper-sword-in.git

Then follow the sword-in software package installation instructions. In particular, ensure lxml is installed, and that the simple-sword-server and other dependencies are installed.
The following commands show what is likely needed, but the sword-in installation documentation should be considered the most up to date:

    sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-devc
    source ../../bin/activate
    pip install -r requirements.txt

Then create a local.cfg file in the sword-in software repository directory and put the following config settings in it (which can be augmented as necessary for future changes):

    PORT = 5001
    JPER_BASE_URL = "https://pubrouter.jisc.ac.uk/api/v1"
    JPER_API_KEY = "admin"
    SWORD2_SERVER_CONFIG['base_url'] = "https://pubrouter.jisc.ac.uk/sword"

Because the sword apps are configured by default on the same machine as the store app, the nginx config file available with the store app 
also contains the configuration necessary to send the /sword route to the sword app. However, this could be separated out should the sword apps
be moved to a separate machine.

And then perform the following commands to run the sword-in app under supervisor:

    pip install gunicorn
    cd /etc/supervisor/conf.d
    sudo ln -s /home/mark/jper-sword-in/src/jper-sword-in/deployment/sword-out.conf .
    sudo supervisorctl reread
    sudo supervisorctl update

NOTE: at this point the sword endpoint will be running, but viewing the URL in a web browser will show an error. This does not strictly matter, 
as the sword server is not a web server; it will still operate as intended. The storage service above contained an nginx configuration that also routes 
requests from the gateway machine to the sword-in code, so that will already be in place. If you have to scale up the services by moving sword-in 
onto a different machine from store, then abstract out the necessary parts of the nginx config too.

ADMIN: The sword-in app should be checked regularly to ensure it is still running, otherwise sword input to the jper app will fail. 
Running it under supervisor should take care of this, but install your own monitoring and alerting software of preference if necessary.


SWORD-OUT

The pattern should be familiar by now, these supporting apps run pretty much the same way:

    virtualenv -p python2.7 jper-sword-out --no-site-packages
    cd jper-sword-out
    mkdir src
    cd src
    git clone https://github.com/JiscPER/jper-sword-out.git
    cd jper-sword-out
    git submodule update --init --recursive
    source ../../bin/activate
    pip install -r requirements.txt
    pip install gunicorn
    cd /etc/supervisor/conf.d
    sudo ln -s /home/mark/jper-sword-out/src/jper-sword-out/deployment/sword-out.conf .
    sudo supervisorctl reread
    sudo supervisorctl update

ADMIN: The sword-out app should be checked regularly because if it is not running then notifications will not be delivered vis SWORD to 
registered repositories.


OAIPMH

The pattern should be familiar by now, these supporting apps run pretty much the same way:

    virtualenv -p python2.7 jper-oaipmh --no-site-packages
    cd jper-oaipmh
    mkdir src
    cd src
    git clone https://github.com/JiscPER/jper-oaipmh.git
    cd jper-oaipmh
    git submodule update --init --recursive
    source ../../bin/activate
    pip install -r requirements.txt
    pip install gunicorn
    cd /etc/supervisor/conf.d
    sudo ln -s /home/mark/jper-oaipmh/src/jper-oaipmh/deployment/oaipmh.conf .
    sudo supervisorctl reread
    sudo supervisorctl update

NOTE:  The storage service above contained an nginx configuration that also routes 
requests forwarded from the gateway machine to the oaipmh code, so that will already be in place. 
If you have to scale up the services by moving oaipmh
onto a different machine from store, then abstract out the necessary parts of the nginx config too.

ADMIN: The oaipmh app should be checked regularly because if it is not running then oaipmh queries to the system will fail.


## ELASTICSEARCH INDEX MACHINE(S)

On the elasticsearch machines, a large disk has been configured at /Index and that is where the elasticsearch indexes should be installed:

    cd /Index
    sudo su
    curl -L https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.5.2.tar.gz -o elasticsearch.tar.gz
    tar -xzvf elasticsearch.tar.gz
    ln -s elasticsearch-1.5.2 elasticsearch
    rm elasticsearch.tar.gz
    cd elasticsearch/bin
    git clone git://github.com/elasticsearch/elasticsearch-servicewrapper.git
    cd elasticsearch-servicewrapper
    mv service ../
    cd ../
    rm -R elasticsearch-servicewrapper
    ln -s /Index/elasticsearch/bin/service/elasticsearch /etc/init.d/elasticsearch
    update-rc.d elasticsearch defaults

Then edit the configs:

    cd /Index/elasticsearch
    vim config/elasticsearch.yml
    
Uncomment bootstrap.mlockall true

Uncomment cluster.name: elasticsearch and change to jper

Uncomment index.number_of_shards and index.number_of_replicas and set to 6 and 1

Uncomment zen ping multicast false

In discovery zen ping unicast hosts put the private IP addresses of all machines in the cluster

    vim bin/service/elasticsearch.conf
    
Set.default.ES_HEAP_SIZE=8096

And set wrapper.logfile.loglevel wrapper.logfile.maxsize wrapper.logfile.maxfiles to WARN 100m and 20

Install the necessary plugins:

    bin/plugin -install mobz/elasticsearch-head
    bin/plugin install elasticsearch/elasticsearch-mapper-attachments/2.4.3

Then change the ownership and restart the index:

    cd /Index
    chown -R mark:mark elasticsearch
    /etc/init.d/elasticsearch restart
    exit
    
After installation on the first index machine, archive and copy the entire elasticsearch directory onto the next machine to be configured to join the elasticsearch cluster.

The elasticsearch indexes are technically transient data, and everything in them could be replicated if the incoming files from publishers are stored. However, any metadata 
coming directly into the jper app native API will exist only the index, and could potentially not have any locally available stored article metadata from which to rebuild. Despite this, the function of the jper app is such that it is supposed to process notifications and route them to institutions if possible, and NOT to do historical routing. So, technically, it is not critical to perform backups of the indexes. But, it may still be a good idea and would certainly be convenient in the event of a disaster.

ADMIN: Make sure the index machines have sufficient disk space attached, and that the elasticsearch software is configured to store indexes in its data directory 
to somewhere on the large disks.

ADMIN: ensure regular backups of the elasticsearch cluster data are successfully made, if deemed necessary. Elasticsearch has multiple backup options, both built-in and external. 
For maximum recoverability, backups should be encrypted and stored in an entirely different system and site from that which runs the cluster.

ADMIN: When introducing new machines to the cluster, update the gateway nginx config so that it knows about the additional machines to which queries can be routed. 
Also, be aware that the logstash server communicates directly to the first elasticsearch index via port 9300 rather than over the 9200 interface, so if the first 
machine is ever decommissioned or has its IP changed, be sure to alter the gateway nginx config to point to the new IP.

ADMIN: make sure there is always enough spare disk space to accommodate the indexes on each machine in the elasticsearch cluster.

ADMIN: make sure there is sufficient memory on the elasticsearch machines to run smoothly. In particular, look out for java pid file dumps appearing in the 
elasticsearch directories - these indicate queries filling all available RAM and causing a java memory dump.

ADMIN: it would be a good idea to install your preferred system monitoring and alerting software, and configuring it to monitor disk and memory usage in particular. CPU usage 
may be useful to track too, but is less likely to be a problem.

ADMIN: managing elasticsearch indexing cluster is an administrative task all to itself. Review the elasticsearch documentation and online resources for further information.

ADMIN: Communication with the index cluster from any machine should be done via http://gateway:9200


## ADMIN: Some thoughts on scaling up

First scale up the machine(s) that already exist. This is by far the easiest approach and with amazon machines is very easy. The ones we 
started with are small to save money, but could be a hundred times bigger, with more RAM and CPU as necessary.

Second move the supporting apps onto separate machines if one server for them ends up with too much load. Particularly with the store server, 
it could take a lot of load and could run on its own larger machine if necessary. This is why the JPER service was designed in a modular fashion, 
so that it would be easy to scale up machines and turn on extra ones to handle the supporting apps as necessary.

Thirdly separate the scheduler from the main JPER app - but NOTE that there is only one main machine configured for sftp and this machine 
is where the scheduler should run. If the JPER app is split onto multiple machines, make sure to configure nginx to only serve the 
account / reports / admin stuff from the one machine. If a user account were changed to a publisher account on a machine that was not the main 
one, the sftp credentials would fail to be created appropriately.

Fourthly scheduler tasks COULD be run on different machines, but care must be taken on how this is configured. The scheduled processes for 
moving ftp files and processing them MUST happen on the scheduler running on the machine where ftp access is possible. However the check_unrouted 
process could run on a different machine. To achieve this, install on multiple machines and use the config settings to enable or disable certain 
scheduled processes on the different machines.


## ADMIN: Notes on tests done

We ran initial tests using JPER in single threaded mode, with only one worker process. This ran fine until we sent it many requests at which point 
we started getting errors - exactly as expected. So we then turned on the multi threading and multiple workers, and ran tests again with no failures.

The first test was of request load, where we sent two requests to the JPER API every 20 seconds for 10 hours. This load was sustained by the one 
server machine (and one supporting app sever) at their current size and configuration without issue. The CPUs showed 100% spikes on occasion, but 
were not pegged at maximum and did not fail. Handling greater load should therefore be easy with simple scaling up of the relatively small machine 
size(s) currently in use.

We then tested sending random file sizes to the API, anything from 0 up to 500MB, for ten hours. These also were processed as expected. Of course, 
keep an eye on disk usage and scale up the attached block devices or delete old files as necessary.

We finally ran a one hour test with 70 fake user accounts, to simulate a load of more users on the system, which causes the matches of incoming 
articles to repositories to require significantly more effort. We sent validation requests every sixty seconds with a maximum file size of 20MB 
and a 80% chance of metadata and format errors (high error rate here causing more load to test), along with creation requests every ten seconds 
with 5% error chance and 20MB max file size, and list requests every five seconds with 5% error rate. This test was run with all supporting 
infrastructure running too (store, oaipmh, jper-sword-in, jper-sword-out) and it ran without any issues for the full hour. All operations were 
carried out successfully. The load on the server was 100% on one CPU for the duration of the test, showing that it is processing everything well 
at full speed and without problems, and a fairly constant memory usage staying under 500MB. This indicates stability. After the test completed the 
server returned to idle within seconds, showing that there was no backlog of processes to catch up with. Overall this was a successful final test.


## ADMIN: Seeing what is going on

The gateway_nginx config file in the jper deployment directory includes subdomain definitions for kibana, index, and store. However on the live 
machine these are commented out so that they do not give unauthorised access to data once it goes into production.

Enabling the kibana subdomain allows viewing the kibana log interface at kibana.pubrouter.jisc.ac.uk. This shows a comprehensive overview of 
all jper logs. See the kibana documentation on the elasticsearch website for further information on how this can be customised.

Enabling the store subdomain allows direct access to the contents of the store folder at store.pubrouter.jisc.ac.uk. This can also just be 
browsed on the local filesystem, so is not so useful, but it is available just in case.

Enabling the index subdomain allows direct access to the elasitcsearch index cluster at index.pubrouter.jisc.ac.uk. This can be useful for 
querying the indexes to see what they contain and to see what is changing. The elasticsearch_head plugin is installed, and can be accessed 
at _plugin/head in order to get an indexes overview. See the elasticsearch_head plugin documentation via the elasticsearch website for more 
information.

The jper logs can also be viewed directly, by default they are written on the app1 machine to /home/mark/jperlog

A quick look at the FTP directories will show if there is anything waiting to be processed from the publishers that submit via FTP. By default 
it is at /Incoming/sftpusers. If the scheduler is running, these directories should be getting regularly emptied so they should not keep filling up.

The /Incoming/ftptmp directory is also the default location where files are put after being moved from the FTP user directories. These files are 
processed in this location and then sent into the jper API, and should then get deleted. So it is possible to see files traversing through these 
directories whilst the scheduler is running, but again files should not be filling up in here as the scheduler should be removing them when it is 
finished processing them.

There is also currently a tmparchive configured at /Incoming/tmparchive. This can be disabled if the system is running well, but has been left enabled 
to assist with any further checks that may be desired. It contains exact copies of everything sent by publishers into their FTP directories, so that 
it is possible to check what they sent before it was processed in any way by the jper systems.





















