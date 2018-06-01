from alerts.alerts_service import AlertsService
from execution.execution_service import ExecutionService
from react.observable import read_until_closed


class FailAlerterFeature:
    def __init__(self,
                 execution_service: ExecutionService,
                 alert_service: AlertsService):
        self._execution_service = execution_service
        self._alert_service = alert_service

    def _subscribe_fail_alerter(self):
        execution_service = self._execution_service
        alert_service = self._alert_service

        def finished(execution_id):
            return_code = execution_service.get_exit_code(execution_id)

            if return_code != 0:
                script_config = execution_service.get_config(execution_id)
                script = str(script_config.name)
                audit_name = execution_service.get_audit_name(execution_id)
                output_stream = execution_service.get_anonymized_output_stream(execution_id)

                title = script + ' FAILED'
                body = 'The script "' + script + '", started by ' + audit_name + \
                       ' exited with return code ' + str(return_code) + '.' + \
                       ' Usually this means an error, occurred during the execution.' + \
                       ' Please check the corresponding logs'

                output_stream_data = read_until_closed(output_stream)
                script_output = ''.join(output_stream_data)

                alert_service.send_alert(title, body, script_output)

        execution_service.add_finish_listener(finished)

    def start(self):
        self._subscribe_fail_alerter()
