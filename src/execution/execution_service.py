import logging
from collections import namedtuple

from typing import Optional, Dict, Callable, Any

from execution.executor import ScriptExecutor
from model import script_config
from utils import audit_utils

LOGGER = logging.getLogger('script_server.execution_service')

_ExecutionInfo = namedtuple('_ExecutionInfo',
                            ['execution_id', 'owner', 'audit_name', 'config', 'audit_command', 'all_audit_names'])


class ExecutionService:
    def __init__(self,
                 id_generator):
        self._id_generator = id_generator

        self._executors = {}  # type: Dict[str, ScriptExecutor]
        self._execution_infos = {}  # type: Dict[str, _ExecutionInfo]

        # active from user perspective:
        #   - either they are running
        #   - OR user haven't yet seen execution results
        self._active_executor_ids = set()

        self._finish_listeners = []
        self._start_listeners = []

    def get_active_executor(self, execution_id):
        if execution_id not in self._active_executor_ids:
            return None

        return self._executors.get(execution_id)

    def start_script(self, config, values, user_id, all_audit_names):
        audit_name = audit_utils.get_audit_name(all_audit_names)

        executor = ScriptExecutor(config, values)
        execution_id = self._id_generator.next_id()

        audit_command = executor.get_secure_command()
        LOGGER.info('Calling script #%s: %s', execution_id, audit_command)

        executor.start()
        self._executors[execution_id] = executor
        self._execution_infos[execution_id] = _ExecutionInfo(
            execution_id=execution_id,
            owner=user_id,
            audit_name=audit_name,
            audit_command=audit_command,
            config=config,
            all_audit_names=all_audit_names)
        self._active_executor_ids.add(execution_id)

        self._add_post_finish_handling(execution_id, executor)

        self._fire_execution_started(execution_id)

        return execution_id

    def stop_script(self, execution_id):
        if execution_id in self._executors:
            self._executors[execution_id].stop()

    def kill_script(self, execution_id):
        if execution_id in self._executors:
            self._executors[execution_id].kill()

    def get_exit_code(self, execution_id):
        return self._get_for_executor(execution_id, lambda e: e.get_return_code())

    def is_running(self, execution_id):
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

    def get_config(self, execution_id) -> Optional[script_config.ConfigModel]:
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.config)

    def is_active(self, execution_id):
        return execution_id in self._active_executor_ids

    def can_access(self, execution_id, user_id):
        execution_info = self._execution_infos.get(execution_id)
        return self._can_access_execution(execution_info, user_id)

    @staticmethod
    def _can_access_execution(execution_info: _ExecutionInfo, user_id):
        return (execution_info is not None) and (execution_info.owner == user_id)

    def get_user_parameter_values(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_user_parameter_values())

    def get_script_parameter_values(self, execution_id):
        return self._get_for_executor(execution_id,
                                      lambda e: e.get_script_parameter_values())

    def get_owner(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.owner)

    def get_audit_name(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.audit_name)

    def get_audit_command(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.audit_command)

    def get_all_audit_names(self, execution_id):
        return self._get_for_execution_info(execution_id,
                                            lambda i: i.all_audit_names)

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

    def cleanup_execution(self, execution_id):
        executor = self._executors.get(execution_id)
        if executor is None:
            return

        if not executor.is_finished():
            raise Exception('Executor ' + execution_id + ' is not yet finished')

        executor.cleanup()
        self._active_executor_ids.remove(execution_id)

    def add_finish_listener(self, callback):
        self._finish_listeners.append(callback)

    def _add_post_finish_handling(self, execution_id, executor):
        self_service = self

        class FinishListener:
            def finished(self):
                self_service._fire_execution_finished(execution_id)

        executor.add_finish_listener(FinishListener())

    def _fire_execution_finished(self, execution_id):
        for callback in self._finish_listeners:
            try:
                callback(execution_id)
            except:
                LOGGER.exception('Could not notify finish listener (%s), execution: %s', str(callback), execution_id)

    def add_start_listener(self, callback):
        self._start_listeners.append(callback)

    def _fire_execution_started(self, execution_id):
        for callback in self._start_listeners:
            try:
                callback(execution_id)
            except:
                LOGGER.exception('Could not notify start listener (%s), execution: %s', str(callback), execution_id)
