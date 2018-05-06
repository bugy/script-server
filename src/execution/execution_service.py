import logging

from alerts.alerts_service import AlertsService
from execution.executor import ScriptExecutor
from execution.logging import ExecutionLoggingService
from react.observable import Observable

LOGGER = logging.getLogger('script_server.execution_service')


class ExecutionService:
    def __init__(self, execution_logging_service, alerts_service, id_generator):
        self._execution_logging_service = execution_logging_service  # type: ExecutionLoggingService
        self._alerts_service = alerts_service  # type: AlertsService
        self._id_generator = id_generator

        self._running_scripts = {}

    def get_active_executor(self, execution_id):
        return self._running_scripts.get(execution_id)

    def start_script(self, config, values, audit_name, all_audit_names):
        script_name = config.name

        executor = ScriptExecutor(config, values, audit_name)
        execution_id = self._id_generator.next_id()

        audit_command = executor.get_secure_command()
        LOGGER.info('Calling script #%s: %s', execution_id, audit_command)

        executor.start()
        self._running_scripts[execution_id] = executor

        secure_output_stream = executor.get_secure_output_stream()

        self._execution_logging_service.start_logging(
            execution_id, audit_name, script_name, audit_command, secure_output_stream, self, all_audit_names)

        self.subscribe_fail_alerter(
            script_name,
            self._alerts_service,
            audit_name,
            executor,
            secure_output_stream)

        return execution_id

    def stop_script(self, execution_id):
        if execution_id in self._running_scripts:
            self._running_scripts[execution_id].stop()

    def kill_script(self, execution_id):
        if execution_id in self._running_scripts:
            self._running_scripts[execution_id].kill()

    def get_exit_code(self, execution_id):
        executor = self._running_scripts.get(execution_id)  # type: ScriptExecutor
        if executor is None:
            return None

        return executor.get_return_code()

    def is_running(self, execution_id):
        executor = self._running_scripts.get(execution_id)  # type: ScriptExecutor
        if executor is None:
            return False

        return not executor.is_finished()

    @staticmethod
    def subscribe_fail_alerter(
            script_name,
            alerts_service,
            audit_name,
            executor: ScriptExecutor,
            output_stream: Observable):

        class Alerter(object):
            def finished(self):
                return_code = executor.get_return_code()

                if return_code != 0:
                    script = str(script_name)

                    title = script + ' FAILED'
                    body = 'The script "' + script + '", started by ' + audit_name + \
                           ' exited with return code ' + str(return_code) + '.' + \
                           ' Usually this means an error, occurred during the execution.' + \
                           ' Please check the corresponding logs'

                    output_stream.wait_close()
                    script_output = ''.join(output_stream.get_old_data())

                    alerts_service.send_alert(title, body, script_output)

        executor.add_finish_listener(Alerter())

    def get_running_processes(self):
        result = []
        for id, executor in self._running_scripts.items():
            if not executor.is_finished():
                result.append(id)

        return result
