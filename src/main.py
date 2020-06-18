import argparse
import json
import logging
import logging.config
import os
import sys

import migrations.migrate
from auth.authorization import create_group_provider, Authorizer
from communications.alerts_service import AlertsService
from config.config_service import ConfigService
from execution.execution_service import ExecutionService
from execution.id_generator import IdGenerator
from execution.logging import ExecutionLoggingService, LogNameCreator, ExecutionLoggingController
from features.executions_callback_feature import ExecutionsCallbackFeature
from features.fail_alerter_feature import FailAlerterFeature
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from files.user_file_storage import UserFileStorage
from model import server_conf
from utils import tool_utils, file_utils
from utils.tool_utils import InvalidWebBuildException
from web import server
from web.client import tornado_client_config

parser = argparse.ArgumentParser(description='Launch script-server.')
parser.add_argument('-d', '--config-dir', default='conf')
parser.add_argument('-f', '--config-file', default='conf.json')
parser.add_argument('-l', '--log-folder', default='logs')
parser.add_argument('-t', '--tmp-folder', default='temp')
args = vars(parser.parse_args())

TEMP_FOLDER = args['tmp_folder']
LOG_FOLDER = args['log_folder']

CONFIG_FOLDER = args['config_dir']
if os.path.isabs(args['config_file']):
    SERVER_CONF_PATH = args['config_file']
else:
    SERVER_CONF_PATH = os.path.join(CONFIG_FOLDER, args['config_file'])

LOGGER = logging.getLogger('main')


def get_secret(secret_file):
    if os.path.exists(secret_file):
        secret = file_utils.read_file(secret_file, byte_content=True)
        if secret:
            return secret

    secret = os.urandom(256)
    file_utils.write_file(secret_file, secret, byte_content=True)
    return secret


def main():
    project_path = os.getcwd()

    try:
        tool_utils.validate_web_build_exists(project_path)
    except InvalidWebBuildException as e:
        print(str(e))
        sys.exit(-1)

    logging_conf_file = os.path.join(CONFIG_FOLDER, 'logging.json')
    with open(logging_conf_file, 'rt') as f:
        log_config = json.load(f)
        file_utils.prepare_folder(LOG_FOLDER)

        logging.config.dictConfig(log_config)

    server_version = tool_utils.get_server_version(project_path)
    logging.info('Starting Script Server' + (', v' + server_version if server_version else ' (custom version)'))

    file_utils.prepare_folder(CONFIG_FOLDER)
    file_utils.prepare_folder(TEMP_FOLDER)

    migrations.migrate.migrate(TEMP_FOLDER, CONFIG_FOLDER, SERVER_CONF_PATH, LOG_FOLDER)

    server_config = server_conf.from_json(SERVER_CONF_PATH, TEMP_FOLDER)

    secret = get_secret(server_config.secret_storage_file)

    tornado_client_config.initialize()

    group_provider = create_group_provider(
        server_config.user_groups, server_config.authenticator, server_config.admin_users)

    authorizer = Authorizer(
        server_config.allowed_users,
        server_config.admin_users,
        server_config.full_history_users,
        group_provider)

    config_service = ConfigService(authorizer, CONFIG_FOLDER)

    alerts_service = AlertsService(server_config.alerts_config)
    alerts_service = alerts_service

    execution_logs_path = os.path.join(LOG_FOLDER, 'processes')
    log_name_creator = LogNameCreator(
        server_config.logging_config.filename_pattern,
        server_config.logging_config.date_format)
    execution_logging_service = ExecutionLoggingService(execution_logs_path, log_name_creator, authorizer)

    existing_ids = [entry.id for entry in execution_logging_service.get_history_entries(None, system_call=True)]
    id_generator = IdGenerator(existing_ids)

    execution_service = ExecutionService(id_generator)

    execution_logging_controller = ExecutionLoggingController(execution_service, execution_logging_service)
    execution_logging_controller.start()

    user_file_storage = UserFileStorage(secret)
    file_download_feature = FileDownloadFeature(user_file_storage, TEMP_FOLDER)
    file_download_feature.subscribe(execution_service)
    file_upload_feature = FileUploadFeature(user_file_storage, TEMP_FOLDER)

    alerter_feature = FailAlerterFeature(execution_service, alerts_service)
    alerter_feature.start()

    executions_callback_feature = ExecutionsCallbackFeature(execution_service, server_config.callbacks_config)
    executions_callback_feature.start()

    server.init(
        server_config,
        server_config.authenticator,
        authorizer,
        execution_service,
        execution_logging_service,
        config_service,
        alerts_service,
        file_upload_feature,
        file_download_feature,
        secret,
        server_version)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
