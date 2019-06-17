from datetime import timezone

from utils import date_utils


class ExecutionInfo(object):
    def __init__(self):
        self.param_values = {}
        self.script = None


def config_to_external(config, id):
    parameters = []
    for parameter in config.parameters:
        external_param = parameter_to_external(parameter)

        if external_param is None:
            continue

        parameters.append(external_param)

    return {
        'id': id,
        'name': config.name,
        'description': config.description,
        'parameters': parameters
    }


def parameter_to_external(parameter):
    if parameter.constant:
        return None

    return {
        'name': parameter.name,
        'description': parameter.description,
        'withoutValue': parameter.no_value,
        'required': parameter.required,
        'default': parameter.default,
        'type': parameter.type,
        'min': parameter.min,
        'max': parameter.max,
        'values': parameter.values,
        'secure': parameter.secure,
        'fileRecursive': parameter.file_recursive,
        'fileType': parameter.file_type
    }


def to_short_execution_log(history_entries, running_script_ids=None):
    if running_script_ids is None:
        running_script_ids = []

    result = []
    for entry in history_entries:
        running = entry.id in running_script_ids
        external_entry = _translate_history_entry(entry, running)
        result.append(external_entry)

    return result


def to_long_execution_log(entry, log, running):
    external_entry = _translate_history_entry(entry, running)
    external_entry['command'] = entry.command
    external_entry['log'] = log

    return external_entry


def _translate_history_entry(entry, running):
    if entry.start_time:
        start_time = date_utils.astimezone(entry.start_time, timezone.utc).isoformat()
    else:
        start_time = None

    return {
        'id': entry.id,
        'startTime': start_time,
        'user': entry.user_name,
        'script': entry.script_name,
        'status': running_flag_to_status(running),
        'exitCode': entry.exit_code
    }


def running_flag_to_status(running):
    return 'running' if running else 'finished'


def to_execution_info(request_parameters):
    NAME_KEY = '__script_name'

    script_name = request_parameters.get(NAME_KEY)

    param_values = {}
    for name, value in request_parameters.items():
        if name == NAME_KEY:
            continue
        param_values[name] = value

    info = ExecutionInfo()
    info.script = script_name
    info.param_values = param_values

    return info


def server_conf_to_external(server_config, server_version):
    return {
        'title': server_config.title,
        'enableScriptTitles': server_config.enable_script_titles,
        'version': server_version
    }
