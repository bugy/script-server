import json
from datetime import timezone

from model import model_helper
from utils import date_utils


class ExecutionInfo(object):
    def __init__(self):
        self.param_values = {}
        self.script = None


def config_to_json(config):
    parameters = []
    for parameter in config.get_parameters():
        if parameter.is_constant():
            continue

        parameters.append({
            "name": parameter.get_name(),
            "description": parameter.get_description(),
            "withoutValue": parameter.is_no_value(),
            "required": parameter.is_required(),
            "default": model_helper.get_default(parameter),
            "type": parameter.type,
            "min": parameter.get_min(),
            "max": parameter.get_max(),
            "values": parameter.get_values(),
            "secure": parameter.secure
        })

    return json.dumps({
        "name": config.get_name(),
        "description": config.get_description(),
        "parameters": parameters
    })


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
        'user': entry.username,
        'script': entry.script_name,
        'status': 'running' if running else 'finished',
        'exitCode': entry.exit_code
    }


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
