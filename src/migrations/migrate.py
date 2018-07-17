import itertools
import json
import logging
import os
import re
from collections import namedtuple, OrderedDict
from datetime import datetime

import execution.logging
from execution.logging import ExecutionLoggingService
from utils import file_utils
from utils.date_utils import sec_to_datetime, to_millis

__migrations_registry = OrderedDict()

_MigrationDescriptor = namedtuple('_MigrationDescriptor', ['id', 'callable', 'name', 'requires'])

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
def __migrate_old_files():
    output_folder = os.path.join('logs', 'processes')
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

        match = re.fullmatch('(.+)_([^_]+)_((\d\d)(\d\d)(\d\d)_(\d\d)(\d\d)(\d\d))', filename)
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
def __migrate_user_id():
    output_folder = os.path.join('logs', 'processes')
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
def __introduce_access_config():
    file_path = os.path.join('conf', 'conf.json')

    if not os.path.exists(file_path):
        return

    content = file_utils.read_file(file_path)
    json_object = json.loads(content)

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
        space_matches = re.findall('^\s+', content, flags=re.MULTILINE)
        if space_matches:
            indent_string = space_matches[0].replace('\t', '    ')
            indent = min(len(indent_string), 8)
        else:
            indent = 4

        with open(file_path, 'w') as fp:
            json.dump(json_object, fp, indent=indent)


def migrate(temp_folder, conf_folder):
    _validate_requirements()

    if _is_new_installation(temp_folder, conf_folder):
        _write_migrations(temp_folder, __migrations_registry.keys())
    else:
        old_migrations = _read_old_migrations(temp_folder)

        to_migrate = [m for m in __migrations_registry.keys() if (m not in old_migrations)]

        if not to_migrate:
            return

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
                migration_descriptor.callable()
                migrated.append(migration_id)
                to_migrate.remove(migration_id)
                _write_migrations(temp_folder, migrated)

                has_changes = True

            if not has_changes:
                raise Exception('Not all migrations were applied. Remaining: ' + str(to_migrate))
