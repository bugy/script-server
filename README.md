# script-server
Script-server provides Web GUI for your scripts and remote execution facility. 

All you need to do, is create link/configuration to your scripts and start the server. Users will be able to access your scripts via web-browser and execute them. 
Everything will run on your machine, so users shouldn't care about setting up an environment or working via ssh.


GUI is very straightforward and easy-to-use for anyone. Example of the user interface:
![Example of user interface](screenshot.png?raw=true)

## Features
1. Users can specify script parameters. Different parameter types are supported [conf-script]
2. Providing immediate output to the user and reading his input (if script is interactive)
3. LDAP authentication support [conf-server]
4. Alerting in case of script execution failures (email or web hook) [conf-server]
5. HTTPS support [conf-server]
6. Transparent logging and auditing
7. Bash colors/styles support [conf-script]
8. Download script execution results [conf-script]

[conf-script] These features are configurable per script, see [script config page](https://github.com/bugy/script-server/wiki/Script-config) for details

[conf-server] These features are configurable for the whole server, see [server config page](https://github.com/bugy/script-server/wiki/Server-config) for details

## Requirements
### Server-side
Python 3.4+ with following modules:
* Tornado
* six

OS support:
- Linux (main). Tested and working on Debian 8,9
- Windows (additional). Light testing on Windows 7
- MacOS (additional). Not tested. Most probably some fixes are needed

### Client-side
Any more or less up to date browser with enabled JS

Internet connection is not needed. All the files are loaded from the server.

## Installation
### Developer mode
1. Clone/download the repository
2. Run tools/init.py script (this will download javascript libraries)

## Setup and run
1. Create configurations for your scripts in *conf/runners/* folder (see [script config page](https://github.com/bugy/script-server/wiki/Script-config) for details)
2. Launch launcher.py from script-server folder
2.1 Windows command: launcher.py
2.2 Linux command: ./launcher.py

By default, server will run on 5000 port, over HTTP protocol.

### Server config
All the features listed above and some other minor features can be configured in *conf/conf.json* file. 
It is allowed not to create this file. In this case default values will be used.
See [server config page](https://github.com/bugy/script-server/wiki/Server-config) for details

#### SSL 
If you want server to work over HTTPS, you should specify server key and certificate in server configuration.

## Security
Completely no security! Use it only in local network for trusted users. 

## Logging
All web/operating logs are written to the *logs/server.log*
Additionally each script logs are written to separate file in *logs/processes*. File name format is {script\_name}\_{client\_address}\_{date}\_{time}.log. 

## Testing/demo
Script-server has bundled configs/scripts for testing/demo purposes, which are located in testing folder. You can link/copy testing config files to server config files.
