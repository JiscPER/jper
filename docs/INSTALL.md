# JPER: System installation

Soon to contain the installation documentation

Set up machines

gateway
app1
app2
index1
index2

gateway receives and routes, and handles secondary tasks like running the logging
apps are configured to talk to each other where necessary and to indexes via the gateway

app1 (and extra instances of it where necessary) run the core jper app

app2 (and extra instances of it where necessary) run the supporting apps - store and sword-in and sword-out
these apps could run on separate app machines if load requires it. But first the machine can just be scaled up.
Load should be low anyway.

index1 and index2 (and extra instances of them if necessary) run the elasticsearch indexes

current setup is on amazon machines running ubuntu 14.04 but could run on similar linux systems on other cloud hosting providers or other sources of linux hardware

