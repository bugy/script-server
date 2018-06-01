import json
import logging
import logging.config
import os

from alerts.alerts_service import AlertsService
from config.config_service import ConfigService
from execution.execution_service import ExecutionService
from execution.id_generator import IdGenerator
from execution.logging import ExecutionLoggingService, LogNameCreator, ExecutionLoggingInitiator
from features.fail_alerter_feature import FailAlerterFeature
from features.file_download_feature import FileDownloadFeature
from features.file_upload_feature import FileUploadFeature
from files.user_file_storage import UserFileStorage
from model import server_conf
from utils import tool_utils, file_utils
from web import server

TEMP_FOLDER = 'temp'

CONFIG_FOLDER = 'conf'
SERVER_CONF_PATH = os.path.join(CONFIG_FOLDER, 'conf.json')
LOGGER = logging.getLogger('main')


def get_secret(temp_folder):
    secret_file = os.path.join(temp_folder, 'secret.dat')
    if os.path.exists(secret_file):
        secret = file_utils.read_file(secret_file, byte_content=True)
        if secret:
            return secret

    secret = os.urandom(256)
    file_utils.write_file(secret_file, secret, byte_content=True)
    return secret


def main():
    tool_utils.validate_web_imports_exist(os.getcwd())

    logging_conf_file = os.path.join(CONFIG_FOLDER, 'logging.json')
    with open(logging_conf_file, 'rt') as f:
        log_config = json.load(f)
        file_utils.prepare_folder(os.path.join('logs'))

        logging.config.dictConfig(log_config)

    file_utils.prepare_folder(CONFIG_FOLDER)
    file_utils.prepare_folder(TEMP_FOLDER)

    server_config = server_conf.from_json(SERVER_CONF_PATH)

    secret = get_secret(TEMP_FOLDER)

    config_service = ConfigService(CONFIG_FOLDER)

    alerts_service = AlertsService(server_config.get_alerts_config())
    alerts_service = alerts_service

    execution_logs_path = os.path.join('logs', 'processes')
    log_name_creator = LogNameCreator(
        server_config.logging_config.filename_pattern,
        server_config.logging_config.date_format)
    execution_logging_service = ExecutionLoggingService(execution_logs_path, log_name_creator)

    existing_ids = [entry.id for entry in execution_logging_service.get_history_entries()]
    id_generator = IdGenerator(existing_ids)

    execution_service = ExecutionService(id_generator)

    execution_logging_initiator = ExecutionLoggingInitiator(execution_service, execution_logging_service)
    execution_logging_initiator.start()

    user_file_storage = UserFileStorage(secret)
    file_download_feature = FileDownloadFeature(user_file_storage, TEMP_FOLDER)
    file_download_feature.subscribe(execution_service)
    file_upload_feature = FileUploadFeature(user_file_storage, TEMP_FOLDER)

    alerter_feature = FailAlerterFeature(execution_service, alerts_service)
    alerter_feature.start()

    server.init(
        server_config,
        execution_service,
        execution_logging_service,
        config_service,
        file_upload_feature,
        file_download_feature,
        secret)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
