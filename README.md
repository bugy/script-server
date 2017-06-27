# script-server
Script-server provides Web GUI for your scripts and remote execution facility. 

All you need to do, is create link/configuration to your scripts and start the server. Users will be able to access your scripts via web-browser and execute them. 
Everything will run on your machine, so users shouldn't care about setting up an environment or working via ssh.


GUI is very straightforward and easy-to-use for anyone. Example of the user interface:
![Example of user interface](https://cloud.githubusercontent.com/assets/1275813/26519407/f0318706-42c0-11e7-8328-34ded505839c.png)

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

Some features can require additional modules. Such requirements are specified in a corresponding feature description.

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
  * Windows command: launcher.py
  * Linux command: ./launcher.py

By default, server will run on 5000 port, over HTTP protocol.

### Server config
All the features listed above and some other minor features can be configured in *conf/conf.json* file. 
It is allowed not to create this file. In this case default values will be used.
See [server config page](https://github.com/bugy/script-server/wiki/Server-config) for details

## Logging
All web/operating logs are written to the *logs/server.log*
Additionally each script logs are written to separate file in *logs/processes*. File name format is {script\_name}\_{client\_address}\_{date}\_{time}.log. 

## Testing/demo
Script-server has bundled configs/scripts for testing/demo purposes, which are located in samples folder. You can link/copy these config files (samples/configs/\*.json) to server config folder (conf/runners).

## Security
General note: for different security reasons it's recommended to run script server only on a trusted network.
### Shell commands injection
Script server guarantees that all user parameters are passed to an executable script as arguments and won't be executed under any conditions. There is no way to inject fraud command from a client side.
However user parameters are not escaped, so scripts should take care of not executing them also (general recommendation for bash is at least to wrap all arguments in double quotes).
It's recommended to use typed parameters when 	appropriate, because they are validated for proper values and so they are harder to be subject of commands injection. Such attempts would be easier to detect also.

_Important!_ Command injection protection is fully supported for linux, but _only_ for .bat and .exe files on Windows

### XSS and CSRF
At the moment script server _is_ vulnerable to these attacks.
