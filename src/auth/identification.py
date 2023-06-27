import abc
import logging
import uuid

from model.trusted_ips import TrustedIpValidator
from utils import tornado_utils, date_utils, audit_utils
from utils.date_utils import days_to_ms
from utils.tornado_utils import can_write_secure_cookie

LOGGER = logging.getLogger('identification')


class Identification(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def identify(self, request_handler):
        pass

    @abc.abstractmethod
    def identify_for_audit(self, request_handler):
        pass


class AuthBasedIdentification(Identification):
    def __init__(self, authentication_provider) -> None:
        self._authentication_provider = authentication_provider

    def identify(self, request_handler):
        current_user = self._authentication_provider.get_username(request_handler)
        if not current_user:
            raise Exception('Not authenticated')
        return current_user

    def identify_for_audit(self, request_handler):
        return self.identify(request_handler)


class IpBasedIdentification(Identification):
    EXPIRES_DAYS = 14
    COOKIE_KEY = 'client_id_token'
    EMPTY_TOKEN = (None, None)

    def __init__(self, ip_validator: TrustedIpValidator, user_header_name) -> None:
        self._ip_validator = ip_validator
        self._user_header_name = user_header_name

    def identify(self, request_handler):
        remote_ip = request_handler.request.remote_ip
        new_trusted = self._ip_validator.is_trusted(remote_ip)

        if new_trusted:
            if request_handler.get_cookie(self.COOKIE_KEY):
                request_handler.clear_cookie(self.COOKIE_KEY)
            if self._user_header_name:
                user_header = request_handler.request.headers.get(self._user_header_name, None)
                if user_header:
                    return user_header
            return self._resolve_ip(request_handler)

        (client_id, days_remaining) = self._read_client_token(request_handler)
        if client_id:
            if days_remaining < (self.EXPIRES_DAYS - 2):
                if self._can_write(request_handler):
                    self._write_client_token(client_id, request_handler)

            return client_id

        if not self._can_write(request_handler):
            raise Exception('Cannot generate ID, because request_handler is not writable')

        ip = self._resolve_ip(request_handler)
        new_id = ip + '-' + uuid.uuid4().hex[:16]

        LOGGER.info('Assigned user_id=%s to %s' % (new_id, str(audit_utils.get_all_audit_names(request_handler))))
        self._write_client_token(new_id, request_handler)

        return new_id

    def identify_for_audit(self, request_handler):
        remote_ip = request_handler.request.remote_ip
        if self._ip_validator.is_trusted(remote_ip) and (self._user_header_name):
            return request_handler.request.headers.get(self._user_header_name, None)
        return None

    def _resolve_ip(self, request_handler):
        proxied_ip = tornado_utils.get_proxied_ip(request_handler)
        if proxied_ip:
            ip = proxied_ip
        else:
            ip = request_handler.request.remote_ip

        return ip

    def _read_client_token(self, request_handler):
        client_id_token = tornado_utils.get_secure_cookie(request_handler, self.COOKIE_KEY)
        if not client_id_token:
            return self.EMPTY_TOKEN

        parts = client_id_token.split('&')
        if len(parts) != 2:
            LOGGER.warning('Invalid token structure: ' + client_id_token)
            return self.EMPTY_TOKEN

        try:
            expiry_time = int(parts[1])
        except:
            LOGGER.exception('Invalid expiry time in: ' + client_id_token)
            return self.EMPTY_TOKEN

        days_remaining = date_utils.ms_to_days(expiry_time - date_utils.get_current_millis())
        if days_remaining < 0:
            LOGGER.warning('Token seems to be expired: ' + str(expiry_time))
            return self.EMPTY_TOKEN

        return parts[0], days_remaining

    def _write_client_token(self, client_id, request_handler):
        expiry_time = date_utils.get_current_millis() + days_to_ms(self.EXPIRES_DAYS)
        new_token = client_id + '&' + str(expiry_time)
        request_handler.set_secure_cookie(self.COOKIE_KEY, new_token, expires_days=self.EXPIRES_DAYS)

    def _can_write(self, request_handler):
        return can_write_secure_cookie(request_handler)
