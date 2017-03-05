# script-server
Script-server provides Web GUI for your scripts and remote execution facility. 

All you need to do, is create link/configuration to your scripts and start the server. Users will be able to access your scripts via web-browser and execute them. 
Everything will run on your machine, so users shouldn't care about setting up an environment or working via ssh.


GUI is very straightforward and easy-to-use for anyone. Example of the user interface:
![Example of user interface](screenshot.png?raw=true)

## Features
1. Users can specify script parameters. Different parameter types are supported
2. Providing immediate output to the user and reading his input (if script is interactive)
3. LDAP authentication support
4. Alerting in case of script execution failures (email or web hook)
5. HTTPS support
6. Transparent logging and auditing

## Setup and run
1. Clone/download the repository
2. Create configurations for your scripts in *conf/runners/* folder (see [script config page](https://github.com/bugy/script-server/wiki/Script-config) for details)
3. Launch server using python3: python launcher.py

By default, server will run on 5000 port, over HTTP protocol

### Server config
You can configure ssl and port, using *conf/conf.json* file. This file should have correct json structure. All missing parameters will be replaced with defaults.
It is allowed not to create this file. In this case default values will be used.
See [server config page](https://github.com/bugy/script-server/wiki/Server-config) for details

#### SSL 
If you want server to work over HTTPS, you should specify server key and certificate in server configuration.

## Requirements
### Server-side
Python 3.5+ with following modules:
* Tornado
* six

OS support:
- Linux (main). Tested and working on Debian 8
- Windows (additional). Light testing on Windows 7
- MacOS (additional). Not tested. Most probably some fixes are needed

### Client-side
Any more or less up to date browser with enabled JS

Internet connection is not needed. All the files are loaded from the server.

## Security
Completely no security! Use it only in local network for trusted users. 

## Logging
All web/operating logs are written to the *logs/server.log*
Additionally each script logs are written to separate file in *logs/processes*. File name format is {script\_name}\_{client\_address}\_{date}\_{time}.log. 

## Testing/demo
Script-server has bundled configs/scripts for testing/demo purposes, which are located in testing folder. You can link/copy testing config files to server config files.
