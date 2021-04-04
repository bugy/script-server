import logging
from collections import namedtuple
from typing import Optional, Dict, Callable, Any

from auth.authorization import Authorizer
from auth.user import User
from execution.executor import ScriptExecutor
from model import script_config
from model.model_helper import is_empty, AccessProhibitedException
from utils.exceptions.missing_arg_exception import MissingArgumentException
from utils.exceptions.not_found_exception import NotFoundException

LOGGER = logging.getLogger('script_server.execution_service')

_ExecutionInfo = namedtuple('_ExecutionInfo',
                            ['execution_id', 'owner_user', 'audit_name', 'config', 'audit_command'])


class ExecutionService:
    def __init__(self, authorizer, id_generator):

        self._id_generator = id_generator
        self._authorizer = authorizer  # type: Authorizer

        self._executors = {}  # type: Dict[str, ScriptExecutor]
        self._execution_infos = {}  # type: Dict[str, _ExecutionInfo]

        # active from user perspective:
        #   - either they are running
        #   - OR user haven't yet seen execution results
        self._active_executor_ids = set()

        self._finish_listeners = []
        self._start_listeners = []

    def get_active_executor(self, execution_id, user):
        self.validate_execution_id(execution_id, user, only_active=False)
        if execution_id not in self._active_executor_ids:
            return None

        return self._executors.get(execution_id)

    def start_script(self, config, values, user: User):
        audit_name = user.get_audit_name()

        executor = ScriptExecutor(config, values)
        execution_id = self._id_generator.next_id()

        audit_command = executor.get_secure_command()
        LOGGER.info('Calling script #%s: %s', execution_id, audit_command)

        executor.start()
        self._executors[execution_id] = executor
        self._execution_infos[execution_id] = _ExecutionInfo(
            execution_id=execution_id,
            owner_user=user,
            audit_name=audit_name,
            audit_command=audit_command,
            config=config)
        self._active_executor_ids.add(execution_id)

        self._add_post_finish_handling(execution_id, executor, user)

        self._fire_execution_started(execution_id, user)

        return execution_id

    def stop_script(self, execution_id, user):
        self.validate_execution_id(execution_id, user)

        if execution_id in self._executors:
            self._executors[execution_id].stop()

    def kill_script(self, execution_id, user):
        self.validate_execution_id(execution_id, user)

        if execution_id in self._executors:
            self._executors[execution_id].kill()

    def kill_script_by_system(self, execution_id):
        if execution_id in self._executors:
            self._executors[execution_id].kill()

    def get_exit_code(self, execution_id):
        return self._get_for_executor(execution_id, lambda e: e.get_return_code())

    def is_running(self, execution_id, user):
        self.validate_execution_id(execution_id, user, only_active=False, allow_when_history_access=True)

        executor = self._executors.get(execution_id)  # type: ScriptExecutor
        if executor is None:
            return False

        return not executor.is_finished()

    def get_active_executions(self, user_id):
        result = []
        for id in self._active_executor_ids:
            execution_info = self._execution_infos[id]

            if self._can_access_execution(execution_info, user_id):
                result.append(id)

        return result

    def get_running_executions(self):
        result = []
        for id, executor in self._executors.items():
            if executor.is_finished():
                continue
            result.append(id)

        return result

    def get_config(self, execution_id, user) -> Optional[script_config.ConfigModel]:
        self.validate_execution_id(execution_id, user)

        return self._get_for_execution_info(execution_id,
                                            lambda i: i.config)

    def is_active(self, execution_id):
        return execution_id in self._active_executor_ids

    def can_access(self, execution_id, user_id):
        execution_info = self._execution_infos.get(execution_id)
        return self._can_access_execution(execution_info, user_id)

    def validate_execution_id(self, execution_id, user, only_active=True, allow_when_history_access=False):
        if is_empty(execution_id):
            raise MissingArgumentException('Execution id is missing', 'execution_id')

        if only_active and (not self.is_active(execution_id)):
            raise NotFoundException('No (active) executor found for id ' + execution_id)

        if not self.can_access(execution_id, user.user_id) \
                and not (allow_when_history_access and self._has_full_history_rights(user.user_id)):
            LOGGER.warning('Prohibited access to not owned execution #%s (user=%s)',
                           execution_id, str(user))
            raise AccessProhibitedException('Prohibited access to not owned execution')

    @staticmethod
    def _can_access_execution(execution_info: _ExecutionInfo, user_id):
        return (execution_info is not None) and (execution_info.owner_user.user_id == user_id)

    def get_user_parameter_values(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_user_parameter_values())

    def get_script_parameter_values(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_script_parameter_values())

    def get_owner(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.owner_user.user_id)

    def get_audit_name(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.owner_user.get_audit_name())

    def get_audit_command(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.audit_command)

    def get_all_audit_names(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.owner_user.audit_names)

    def get_anonymized_output_stream(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_anonymized_output_stream())

    def get_raw_output_stream(self, execution_id, user_id):
        owner = self.get_owner(execution_id)

        def getter(executor):
            if user_id != owner:
                LOGGER.warning(user_id + ' tried to access execution #' + execution_id + ' with owner ' + owner)
            return executor.get_raw_output_stream()

        return self._get_for_executor(execution_id, getter)

    def get_process_id(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_process_id())

    def _get_for_executor(self, execution_id, getter: Callable[[ScriptExecutor], Any]):
        executor = self._executors.get(execution_id)
        if executor is None:
            return None

        return getter(executor)

    def _get_for_execution_info(self, execution_id, getter: Callable[[_ExecutionInfo], Any]):
        info = self._execution_infos.get(execution_id)
        if info is None:
            return None

        return getter(info)

    def cleanup_execution(self, execution_id, user):
        try:
            self.validate_execution_id(execution_id, user)
        except NotFoundException:
            return

        executor = self._executors.get(execution_id)

        if not executor.is_finished():
            raise Exception('Executor ' + execution_id + ' is not yet finished')

        executor.cleanup()
        self._active_executor_ids.remove(execution_id)

    def add_finish_listener(self, callback, execution_id=None):
        if execution_id is None:
            self._finish_listeners.append(callback)

        else:
            executor = self._executors.get(execution_id)
            if not executor:
                LOGGER.error('Failed to find executor for id ' + execution_id)
                return

            class FinishListener:
                def finished(self):
                    callback()

            executor.add_finish_listener(FinishListener())

    def _add_post_finish_handling(self, execution_id, executor, user):
        self_service = self

        class FinishListener:
            def finished(self):
                self_service._fire_execution_finished(execution_id, user)

        executor.add_finish_listener(FinishListener())

    def _fire_execution_finished(self, execution_id, user):
        for callback in self._finish_listeners:
            try:
                callback(execution_id, user)
            except:
                LOGGER.exception('Could not notify finish listener (%s), execution: %s', str(callback), execution_id)

    def add_start_listener(self, callback):
        self._start_listeners.append(callback)

    def _fire_execution_started(self, execution_id, user):
        for callback in self._start_listeners:
            try:
                callback(execution_id, user)
            except:
                LOGGER.exception('Could not notify start listener (%s), execution: %s', str(callback), execution_id)

    def _has_full_history_rights(self, user_id):
        return self._authorizer.has_full_history_access(user_id)
