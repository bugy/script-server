import json
import os
import queue
import subprocess
import threading
import traceback

import six
from flask import Flask, request, send_from_directory, abort, Response

import configs_model
import execution
import external_model
import utils.file_utils as file_utils

app = Flask(__name__)
running_scripts = {}


def read_configs():
    configs_dir = "configs"
    files = os.listdir(configs_dir)

    configs = [file for file in files if file.lower().endswith(".json")]

    result = []

    for config_path in configs:
        path = os.path.join(configs_dir, config_path)
        content = file_utils.read_file(path)
        result.append(configs_model.from_json(path, content))

    return result


@app.route("/scripts/list", methods=["GET"])
def get_scripts():
    configs = read_configs()

    return json.dumps([config.get_name() for config in configs])


@app.route("/scripts/info", methods=["GET"])
def get_script_info():
    params = request.values

    if not ("name" in params):
        return abort("Name is not specified")

    name = params["name"]

    config = find_config_by_name(name)

    if not config:
        return "Couldn't find a script by name"

    return external_model.config_to_json(config)


def find_config_by_name(name):
    configs = read_configs()
    config_by_name = None
    for config in configs:
        if config.get_name() == name:
            config_by_name = config
            break
    return config_by_name


@app.route("/<path:filename>")
def web_resources(filename):
    if not filename:
        filename = "index.html"

    return send_from_directory("web", filename)


def build_parameter_string(param_values, config):
    result = []

    for parameter in config.get_parameters():
        name = parameter.get_name()

        if name in param_values:
            value = param_values[name]

            if parameter.is_no_value():
                # do not replace == True, since REST service can start accepting boolean as string
                if (value == True) or (value == "true"):
                    result.append(parameter.get_param())
            else:
                if value:
                    result.append(parameter.get_param())

                    # value_string = '"' + value.replace("\"", "\\\"") + '"'
                    # result.append(value_string)
                    result.append(value)

    return result


@app.route("/scripts/execute/input", methods=["POST"])
def post_user_input():
    request_data = request.data.decode("UTF-8")
    process_id = json.loads(request_data).get("processId")
    value = json.loads(request_data).get("value")

    running_scripts[process_id].write_to_input(value)

    return ""


@app.route("/scripts/execute/stop", methods=["POST"])
def stop_script():
    process_id = int(request.data.decode("UTF-8"))

    running_scripts[process_id].stop()

    return ""


@app.route("/scripts/execute", methods=["POST"])
def execute_script():
    request_data = request.data.decode("UTF-8")

    execution_info = external_model.to_execution_info(request_data)

    script_name = execution_info.get_script()

    config = find_config_by_name(script_name)

    if not config:
        return abort("Script with name '" + str(script_name) + "' not found")

    try:
        script_path = file_utils.normalize_path(config.get_script_path())
        script_args = build_parameter_string(execution_info.get_param_values(), config)

        command = []
        command.append(script_path)
        command.extend(script_args)

        six.print_("Calling script: " + " ".join(command))

        process = subprocess.Popen(command,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)

        process_wrapper = execution.ProcessWrapper(process)
        process_id = process_wrapper.get_process_id()

        running_scripts[process_id] = process_wrapper

        output = queue.Queue()

        output.put(json.dumps({
            "processId": process_id
        }))

        output.put(json.dumps({
            "input": "your input >>",
        }))

        output.put(wrap_script_output(" ---  OUTPUT  --- \n"))

        from_process = threading.Thread(target=pipe_process_to_http, args=(process_wrapper, output))
        from_process.start()

        def response_stream():
            while True:
                try:
                    output_object = output.get(timeout=1)
                    yield output_object
                except queue.Empty:
                    if process_wrapper.is_finished():
                        break

        return Response(response_stream(), mimetype='text/html')

    except Exception as e:
        traceback.print_exc()
        if (hasattr(e, "strerror") and e.strerror):
            error_output = e.strerror
        else:
            error_output = "Unknown error occurred, contact the administrator"

        result = " ---  ERRORS  --- \n"
        result += error_output

        return wrap_script_output(result)


def pipe_process_to_http(process_wrapper: execution.ProcessWrapper, output):
    while not process_wrapper.is_finished():
        process_output = process_wrapper.read()

        if not (process_output is None):
            output.put(wrap_script_output(process_output))


def wrap_script_output(text):
    return json.dumps({
        "output": text
    })


def main():
    app.debug = True
    app.run(threaded=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
