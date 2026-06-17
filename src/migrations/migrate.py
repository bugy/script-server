import itertools
import json
import logging
import os
import re
from collections import namedtuple, OrderedDict
from datetime import datetime

import execution.logging
import utils.custom_json as custom_json
from execution.logging import ExecutionLoggingService
from model import model_helper
from utils import file_utils
from utils.date_utils import sec_to_datetime, to_millis
from utils.string_utils import is_blank

__migrations_registry = OrderedDict()

_MigrationDescriptor = namedtuple('_MigrationDescriptor', ['id', 'callable', 'name', 'requires'])

_Context = namedtuple('_Context', ['temp_folder', 'conf_folder', 'conf_file', 'log_folder'])

LOGGER = logging.getLogger('migrations')


def _add_to_registry(migration, id, requires):
    if id in __migrations_registry:
        raise Exception('Duplicated id found: ' + id)

    __migrations_registry[id] = _MigrationDescriptor(id, migration, migration.__name__, requires)


def _migration(id, requires=None):
    def decorator(func):
        _add_to_registry(func, id, requires)

        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def _is_new_folder(folder):
    if not os.path.exists(folder):
        return True

    if os.path.isdir(folder):
        for root, subdirs, files in os.walk(folder):
            if len(files) > 0:
                return False

            return True

    raise Exception(folder + ' should be a directory')


def _is_new_installation(temp_folder, conf_folder):
    return _is_new_folder(temp_folder) and _is_new_folder(conf_folder)


def _read_old_migrations(temp_folder):
    file_path = os.path.join(temp_folder, 'migrations.txt')

    if not os.path.exists(file_path):
        return []

    content = file_utils.read_file(file_path)
    if not content:
        return []

    return [id.strip() for id in content.split('\n') if id.strip()]


def _write_migrations(temp_folder, migrations):
    file_path = os.path.join(temp_folder, 'migrations.txt')
    file_utils.write_file(file_path, '\n'.join(migrations))


def _validate_requirements():
    for id, descriptor in __migrations_registry.items():
        if not descriptor.requires:
            continue

        for requirement in descriptor.requires:
            if requirement not in __migrations_registry.keys():
                raise Exception('Migration ' + id + ' has unknown requirement ' + requirement)


@_migration('add_execution_info_to_log_files')
def __migrate_old_files(context):
    output_folder = os.path.join(context.log_folder, 'processes')
    if not os.path.exists(output_folder):
        return

    log_files = [os.path.join(output_folder, file)
                 for file in os.listdir(output_folder)
                 if file.lower().endswith('.log')]

    def is_new_format(log_file):
        with open(log_file, 'r') as f:
            first_line = f.readline().strip()

            if not first_line.startswith('id:'):
                return False

            for line in f:
                if line.strip() == execution.logging.OUTPUT_STARTED_MARKER:
                    return True

        return False

    old_files = [log_file for log_file in log_files if not is_new_format(log_file)]

    if not old_files:
        return

    existing_ids = set()
    for file in log_files:
        correct, parameters_text = ExecutionLoggingService._read_parameters_text(file)
        if not correct:
            continue

        parameters = ExecutionLoggingService._parse_history_parameters(parameters_text)
        if not parameters or 'id' not in parameters:
            continue

        existing_ids.add(parameters['id'])

    id_generator = (str(id) for id in itertools.count())
    id_generator = filter(lambda id: id not in existing_ids, id_generator)

    for old_file in old_files:
        log_basename = os.path.basename(old_file)
        filename = os.path.splitext(log_basename)[0]

        match = re.fullmatch(r'(.+)_([^_]+)_((\d\d)(\d\d)(\d\d)_(\d\d)(\d\d)(\d\d))', filename)
        if match:
            script_name = match.group(1)
            username = match.group(2)
            start_time = datetime.strptime(match.group(3), '%y%m%d_%H%M%S')
            id = next(id_generator)
        else:
            script_name = 'unknown'
            username = 'unknown'
            start_time = sec_to_datetime(os.path.getctime(old_file))
            id = next(id_generator)

        new_begin = ''
        new_begin += 'id:' + id + '\n'
        new_begin += 'user_name:' + username + '\n'
        new_begin += 'user_id:' + username + '\n'
        new_begin += 'script:' + script_name + '\n'
        new_begin += 'start_time:' + str(to_millis(start_time)) + '\n'
        new_begin += 'command:unknown' + '\n'
        new_begin += execution.logging.OUTPUT_STARTED_MARKER + '\n'

        file_content = file_utils.read_file(old_file)
        file_content = new_begin + file_content
        file_utils.write_file(old_file, file_content)


@_migration('add_user_id_to_log_files', requires=['add_execution_info_to_log_files'])
def __migrate_user_id(context):
    output_folder = os.path.join(context.log_folder, 'processes')
    if not os.path.exists(output_folder):
        return

    log_files = [os.path.join(output_folder, file)
                 for file in os.listdir(output_folder)
                 if file.lower().endswith('.log')]

    for log_file in log_files:
        (correct, parameters_text) = ExecutionLoggingService._read_parameters_text(log_file)
        if not correct:
            continue

        parameters = ExecutionLoggingService._parse_history_parameters(parameters_text)
        if not parameters or ('user' not in parameters):
            continue

        if ('user_id' in parameters) and ('user_name' in parameters):
            continue

        file_content = file_utils.read_file(log_file, keep_newlines=True)

        file_parts = file_content.split(execution.logging.OUTPUT_STARTED_MARKER + os.linesep, 1)
        parameters_text = file_parts[0]

        user = parameters['user']

        if 'user_id' not in parameters:
            parameters_text += 'user_id:' + user + os.linesep

        if 'user_name' not in parameters:
            parameters_text += 'user_name:' + user + os.linesep

        new_content = parameters_text + execution.logging.OUTPUT_STARTED_MARKER + os.linesep + file_parts[1]
        file_utils.write_file(log_file, new_content.encode(execution.logging.ENCODING), byte_content=True)


@_migration('introduce_access_config')
def __introduce_access_config(context):
    file_path = context.conf_file

    if not os.path.exists(file_path):
        return

    content = file_utils.read_file(file_path)
    json_object = custom_json.loads(content, object_pairs_hook=OrderedDict)

    def move_to_access(field, parent_object):
        if 'access' not in json_object:
            json_object['access'] = {}

        json_object['access'][field] = parent_object[field]
        del parent_object[field]

    changed = False

    if 'auth' in json_object:
        auth_object = json_object['auth']
        if 'allowed_users' in auth_object:
            move_to_access('allowed_users', auth_object)
            changed = True

    fields = ['admin_users', 'trusted_ips']
    for field in fields:
        if field in json_object:
            changed = True
            move_to_access(field, json_object)

    if changed:
        _write_json(file_path, json_object, content)


@_migration('migrate_output_files_parameters_substitution')
def __migrate_output_files_parameters_substitution(context):
    for (conf_file, json_object, content) in _load_runner_files(context.conf_folder):
        if ('output_files' not in json_object) or ('parameters' not in json_object):
            continue

        output_files = json_object['output_files']
        parameter_names = [p['name'] for p in json_object['parameters'] if not is_blank(p.get('name'))]

        changed = False

        for i in range(len(output_files)):
            output_file = output_files[i]

            if not isinstance(output_file, str):
                continue

            for param_name in parameter_names:
                output_file = re.sub('\\$\\$\\$' + param_name, '${' + param_name + '}', output_file)

            if output_file != output_files[i]:
                output_files[i] = output_file
                changed = True

        if changed:
            _write_json(conf_file, json_object, content)


# 1.16 -> 1.17 migration
@_migration('migrate_bash_formatting_to_output_format')
def __migrate_bash_formatting_to_output_format(context):
    for (conf_file, json_object, content) in _load_runner_files(context.conf_folder):
        if 'bash_formatting' not in json_object:
            continue

        if model_helper.read_bool_from_config('bash_formatting', json_object, default=True) is False:
            output_format = 'text'
        else:
            output_format = 'terminal'

        del json_object['bash_formatting']
        json_object['output_format'] = output_format

        _write_json(conf_file, json_object, content)


# 1.16 -> 1.17 migration
@_migration('migrate_repeat_param_and_same_arg_param')
def __migrate_repeat_param_and_same_arg_param(context):
    for (conf_file, json_object, content) in _load_runner_files(context.conf_folder):
        parameters = json_object.get('parameters')
        if not parameters:
            continue

        has_changes = False
        for parameter in parameters:
            repeat_param = model_helper.read_bool_from_config('repeat_param', parameter)
            same_arg_param = model_helper.read_bool_from_config('same_arg_param', parameter)
            multiple_arguments = model_helper.read_bool_from_config('multiple_arguments', parameter)

            if repeat_param is None and same_arg_param is None and multiple_arguments is None:
                continue

            has_changes = True

            if repeat_param is not None:
                del parameter['repeat_param']

            if same_arg_param is not None:
                del parameter['same_arg_param']

            if multiple_arguments is not None:
                del parameter['multiple_arguments']

            if repeat_param is not None:
                parameter['same_arg_param'] = not repeat_param

            if same_arg_param:
                parameter['multiselect_argument_type'] = 'repeat_param_value'
            elif multiple_arguments:
                parameter['multiselect_argument_type'] = 'argument_per_value'

        if has_changes:
            _write_json(conf_file, json_object, content)


@_migration('migrate_ldap_username_pattern_to_user_resolver')
def __migrate_ldap_username_pattern_to_user_resolver(context):
    """Migrate LDAP auth configuration to move username_pattern into ldap_user_resolver"""
    file_path = context.conf_file

    if not os.path.exists(file_path):
        return

    content = file_utils.read_file(file_path)
    try:
        json_object = custom_json.loads(content, object_pairs_hook=OrderedDict)
    except:
        LOGGER.exception('Failed to load config file for LDAP migration: ' + file_path)
        return

    if 'auth' not in json_object:
        return

    auth_config = json_object['auth']
    if not isinstance(auth_config, dict):
        return

    if auth_config.get('type') != 'ldap':
        return

    if 'username_pattern' not in auth_config:
        return
    if 'ldap_user_resolver' in auth_config and 'username_pattern' in auth_config['ldap_user_resolver']:
        return

    username_pattern = auth_config['username_pattern']
    del auth_config['username_pattern']

    if 'ldap_user_resolver' not in auth_config:
        auth_config['ldap_user_resolver'] = {}

    auth_config['ldap_user_resolver']['username_pattern'] = username_pattern

    LOGGER.info('Migrating LDAP username_pattern to ldap_user_resolver in ' + file_path)
    _write_json(file_path, json_object, content)


def _write_json(file_path, json_object, old_content):
    space_matches = re.findall(r'^\s+', old_content, flags=re.MULTILINE)
    if space_matches:
        indent_string = space_matches[0].replace('\t', '    ')
        indent = min(len(indent_string), 8)
    else:
        indent = 4
    with open(file_path, 'w') as fp:
        json.dump(json_object, fp, indent=indent)


def _load_runner_files(conf_folder):
    runners_folder = os.path.join(conf_folder, 'runners')

    if not os.path.exists(runners_folder):
        return []

    conf_files = [os.path.join(runners_folder, file)
                  for file in os.listdir(runners_folder)
                  if file.lower().endswith('.json')]
    conf_files = [f for f in conf_files if not file_utils.is_broken_symlink(f)]

    result = []

    for conf_file in conf_files:
        content = file_utils.read_file(conf_file)
        try:
            json_object = custom_json.loads(content, object_pairs_hook=OrderedDict)
            result.append((conf_file, json_object, content))
        except:
            LOGGER.exception('Failed to load file for migration: ' + conf_file)
            continue

    return result


def migrate(temp_folder, conf_folder, conf_file, log_folder):
    _validate_requirements()

    if _is_new_installation(temp_folder, conf_folder):
        _write_migrations(temp_folder, __migrations_registry.keys())
    else:
        old_migrations = _read_old_migrations(temp_folder)

        to_migrate = [m for m in __migrations_registry.keys() if (m not in old_migrations)]

        if not to_migrate:
            return

        context = _Context(temp_folder, conf_folder, conf_file, log_folder)

        migrated = list(old_migrations)

        has_changes = True
        while has_changes and to_migrate:
            has_changes = False
            for migration_id in to_migrate:
                migration_descriptor = __migrations_registry[migration_id]

                requirements = migration_descriptor.requires
                if requirements and any(req not in migrated for req in requirements):
                    continue

                LOGGER.info('Applying migration ' + str(migration_id))
                migration_descriptor.callable(context)
                migrated.append(migration_id)
                to_migrate.remove(migration_id)
                _write_migrations(temp_folder, migrated)

                has_changes = True

            if not has_changes:
                raise Exception('Not all migrations were applied. Remaining: ' + str(to_migrate))
