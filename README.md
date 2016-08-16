# script-server
This is a simple web-server for hosting and executing scripts on a machine, providing control and output to remote users.
Using the script server you can create scripts on a machine with all the needed packages, configs, etc. All users will be able to execute the scripts without any system requirements (except browser) and in user-friendly interface.

## Requirements
Python 3. Modules:
* Tornado
Potentially should work on any OS, but was tested on Debian 8 only. 

## Secutiry
Completely no security! Use it only in local network for fully trusted users. 

## Setup and run
1. Clone/download the repository
2. Create GUI configs for your scripts in _server-path_/configs folder (see config structure)
3. Launch server using python3: python launcher.py
Server will be running on 5000 port.

## Config structure
{
  /**
    * Required: no
    * Description: user-friendly script name. Will be displayed to user 
    * Type: string
    * Default: script_path filename without extension
    */
  "name": "My example script",
  /**
    * Required: YES
    * Description: path to the script (relative to working directory)
    * Type: string
    */
  "script_path": "/some/path/to/script.sh",
  /**
    * Required: no
    * Description: user-friendly script description, which will be shown to a user
    * Type: string
    */
  "description": "Some useful description on what the script does",
  /**
    * Required: no
    * Description: if the script should be run in emulated terminal (if it has special behaviour in terminal).
    * Type: boolean
    * Default: true
    */
  "requires_terminal": true,
    /**
    * Required: no
    * Description: allows to specify working directory of the script.
    * Type: string
    * Default: the working directory, from which the server was started
    */
  "working_directory": "/home/me/temp",
  /**
    * Required: no
    * Description: list of script parameters
    * Type: array
    */
  "parameters": [
  
  ]
}


## Logging
All web/operating logs are written to the _server-path_/logs/server.log
Additionally each script execution logs (output and error streams) are written to separate file in _server-path_/logs/processes. File name format is {script\_name}\_{client\_address}\_{date}\_{time}.log. 

## Testing/demo
Script-server has bundled configs/scripts for testing/demo purposes, which are located in testing folder. You can link/copy testing config files to server config files.
