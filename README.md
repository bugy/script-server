[![Build Status](https://travis-ci.org/bugy/script-server.svg?branch=master)](https://travis-ci.org/bugy/script-server)

# script-server
Script-server is a Web GUI and a web server for scripts.  

For users it's just a web page, where he specifies script parameters and executes them.  
For system administrators it's a possibility to share their scripts with users, without the need to set up an environment or properly adjust ssh access rights.  

No script modifications are needed - you add a configuration for each script to the script-server and it takes care of proper UI, validation, execution, etc.  

Example of the user interface during script execution:
![Example of user interface](https://cloud.githubusercontent.com/assets/1275813/26519407/f0318706-42c0-11e7-8328-34ded505839c.png)

## Features
- Interactive output/input web console
- Configurable Access
- Auth (optional): LDAP and Google OAuth
- Different script parameter types
- Alerts
- Logging and auditing
- Formatted output support (colors, styles, caret positioning)
- Download of script output files
- Admin page (admin.html) with script execution logs

The features can be configured [per-script](https://github.com/bugy/script-server/wiki/Script-config) or for [the server](https://github.com/bugy/script-server/wiki/Server-config)

## Requirements
### Server-side
Python 3.4 or higher with the following modules:
* Tornado 4/5
* typing *(for python 3.4 only)*

Some features can require additional modules. Such requirements are specified in a corresponding feature description.

OS support:
- Linux (main). Tested and working on Debian 9,10
- Windows (additional). Light testing on Windows 7
- MacOS (additional). Not tested. Most probably some fixes are needed

### Client-side
Any more or less up to date browser with enabled JS

Internet connection is not needed. All the files are loaded from the server.

## Installation
### For production
1. Download script-server.zip file from [Latest release](https://github.com/bugy/script-server/releases/latest) or [Dev release](https://github.com/bugy/script-server/releases/tag/dev)
2. Create script-server folder anywhere on your PC and extract zip content to this folder

(For detailed steps on linux with virtualenv, please see [Installation guide](https://github.com/bugy/script-server/wiki/Installing-on-virtualenv-(linux)))

### For development
1. Clone/download the repository
2. Run 'tools/init.py --dev --no-npm' script

`init.py` script should be run after pulling any new changes

If you are making changes to web files, use `npm run build:dev` or `npm run start:dev`

## Setup and run
1. Create configurations for your scripts in *conf/runners/* folder (see [script config page](https://github.com/bugy/script-server/wiki/Script-config) for details)
2. Launch launcher.py from script-server folder
  * Windows command: launcher.py
  * Linux command: ./launcher.py

By default, server will run on http://localhost:5000

### Server config
All the features listed above and some other minor features can be configured in *conf/conf.json* file. 
It is allowed not to create this file. In this case default values will be used.
See [server config page](https://github.com/bugy/script-server/wiki/Server-config) for details

### Admin panel
Admin panel is accessible on admin.html page (e.g. http://localhost:5000/admin.html)

## Logging
All web/operating logs are written to the *logs/server.log*
Additionally each script logs are written to separate file in *logs/processes*. File name format is {script\_name}\_{client\_address}\_{date}\_{time}.log. 

## Testing/demo
Script-server has bundled configs/scripts for testing/demo purposes, which are located in samples folder. You can link/copy these config files (samples/configs/\*.json) to server config folder (conf/runners).

## Security
I do my best to make script-server secure and invulnerable to attacks, injections or user data security. However to be on safe side, it's better to run script server only on a trusted network.  
Any security leaks report or recommendations are greatly appreciated!
### Shell commands injection
Script server guarantees that all user parameters are passed to an executable script as arguments and won't be executed under any conditions. There is no way to inject fraud command from a client side.
However user parameters are not escaped, so scripts should take care of not executing them also (general recommendation for bash is at least to wrap all arguments in double quotes).
It's recommended to use typed parameters when 	appropriate, because they are validated for proper values and so they are harder to be subject of commands injection. Such attempts would be easier to detect also.

_Important!_ Command injection protection is fully supported for linux, but _only_ for .bat and .exe files on Windows

### XSS and CSRF
At the moment script server _is_ vulnerable to these attacks.
