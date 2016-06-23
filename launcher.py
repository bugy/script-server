import json
import logging
import logging.config
import os
import threading
from datetime import date

import tornado.escape
import tornado.httpserver as httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import configs_model
import execution
import external_model
import utils.file_utils as file_utils

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


class GetScripts(tornado.web.RequestHandler):
    def get(self):
        configs = read_configs()

        self.write(json.dumps([config.get_name() for config in configs]))


class GetScriptInfo(tornado.web.RequestHandler):
    def get(self):
        try:
            name = self.get_query_argument("name")
        except tornado.web.MissingArgumentError:
            respond_error(self, 400, "Script name is not specified")
            return

        config = find_config_by_name(name)

        if not config:
            respond_error(self, 400, "Couldn't find a script by name")
            return

        self.write(external_model.config_to_json(config))


def find_config_by_name(name):
    configs = read_configs()
    config_by_name = None
    for config in configs:
        if config.get_name() == name:
            config_by_name = config
            break
    return config_by_name


def build_parameter_string(param_values, config):
    result = []

    for parameter in config.get_parameters():
        name = parameter.get_name()

        if parameter.is_constant():
            param_values[parameter.name] = parameter.get_default()

        if name in param_values:
            value = param_values[name]

            if parameter.is_no_value():
                # do not replace == True, since REST service can start accepting boolean as string
                if (value == True) or (value == "true"):
                    result.append(parameter.get_param())
            else:
                if value:
                    if parameter.get_param():
                        result.append(parameter.get_param())

                    result.append(value)

    return result


def stop_script(process_id):
    if process_id in running_scripts:
        running_scripts[process_id].stop()


class ScriptStop(tornado.web.RequestHandler):
    def post(self):
        request_body = self.request.body.decode("UTF-8")
        process_id = json.loads(request_body).get("processId")

        if (process_id):
            stop_script(int(process_id))
        else:
            respond_error(self, 400, "Invalid stop request")
            return


class ScriptStreamsSocket(tornado.websocket.WebSocketHandler):
    process_wrapper = None
    reading_thread = None

    def open(self, process_id):
        self.process_wrapper = running_scripts.get(int(process_id))

        if not self.process_wrapper:
            raise Exception("Couldn't find corresponding process")

        self.write_message(wrap_to_server_event("input", "your input >>"))

        self.write_message(wrap_script_output(" ---  OUTPUT  --- \n"))

        reading_thread = threading.Thread(target=pipe_process_to_http, args=(
            self.process_wrapper,
            self.safe_write
        ))
        reading_thread.start()

        web_socket = self

        class FinishListener(object):
            def finished(self):
                reading_thread.join()
                web_socket.close()

        self.process_wrapper.add_finish_listener(FinishListener())

    def on_message(self, text):
        self.process_wrapper.write_to_input(text)

    def on_close(self):
        if not self.process_wrapper.is_finished():
            self.process_wrapper.kill()

    def safe_write(self, message):
        if self.ws_connection is not None:
            self.write_message(message)


class ScriptExecute(tornado.web.RequestHandler):
    process_wrapper = None

    def post(self):
        try:
            request_data = self.request.body

            execution_info = external_model.to_execution_info(request_data.decode("UTF-8"))

            script_name = execution_info.get_script()

            config = find_config_by_name(script_name)

            if not config:
                respond_error(self, 400, "Script with name '" + str(script_name) + "' not found")

            working_directory = config.get_working_directory()
            if working_directory is not None:
                working_directory = file_utils.normalize_path(working_directory)

            script_path = file_utils.normalize_path(config.get_script_path(), working_directory)

            script_args = build_parameter_string(execution_info.get_param_values(), config)

            command = []
            command.append(script_path)
            command.extend(script_args)

            script_logger = logging.getLogger("scriptServer")
            script_logger.info("Calling script: " + " ".join(command))

            if config.is_requires_terminal():
                self.process_wrapper = execution.PtyProcessWrapper(command, config.get_name(),
                                                                   working_directory)
            else:
                self.process_wrapper = execution.POpenProcessWrapper(command, config.get_name(),
                                                                     working_directory)

            process_id = self.process_wrapper.get_process_id()

            running_scripts[process_id] = self.process_wrapper

            self.write(str(process_id))

        except Exception as e:
            script_logger = logging.getLogger("scriptServer")
            script_logger.exception("Error while calling the script")

            if hasattr(e, "strerror") and e.strerror:
                error_output = e.strerror
            else:
                error_output = "Unknown error occurred, contact the administrator"

            result = " ---  ERRORS  --- \n"
            result += error_output

            respond_error(self, 500, result)


def respond_error(request_handler, status_code, message):
    request_handler.set_status(status_code)
    request_handler.write(message)


def wrap_script_output(text):
    return wrap_to_server_event("output", text)


def wrap_to_server_event(event_type, data):
    return json.dumps({
        "event": event_type,
        "data": str(data)
    })


def pipe_process_to_http(process_wrapper: execution.ProcessWrapper, write_callback):
    date_string = date.today().strftime("%y%m%d")
    logger_name = 'process_' + str(process_wrapper.get_process_id()) + "_" + date_string

    log_file = open("logs/processes/" + logger_name + '.log', "w")

    try:
        while True:
            process_output = process_wrapper.read()

            if process_output is not None:
                write_callback(wrap_script_output(process_output))
                log_file.write(process_output)
                log_file.flush()
            else:
                if process_wrapper.is_finished():
                    break
    finally:
        log_file.close()


application = tornado.web.Application([
    (r"/scripts/list", GetScripts),
    (r"/scripts/info", GetScriptInfo),
    (r"/scripts/execute", ScriptExecute),
    (r"/scripts/execute/stop", ScriptStop),
    (r"/scripts/execute/io/(.*)", ScriptStreamsSocket),
    (r"/", tornado.web.RedirectHandler, {"url": "/index.html"}),
    (r"/(.*)", tornado.web.StaticFileHandler, {"path": "web"})
])


def main():
    with open("logging.json", "rt") as f:
        config = json.load(f)
        file_utils.prepare_folder("logs/processes")

        logging.config.dictConfig(config)

    http_server = httpserver.HTTPServer(application)
    http_server.listen(5000)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
