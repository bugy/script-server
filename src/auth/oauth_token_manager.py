import datetime
import logging
from typing import Dict, Optional

import tornado.ioloop

from auth.oauth_token_response import OAuthTokenResponse
from scheduling.scheduler import Scheduler
from utils.tornado_utils import get_secure_cookie, can_write_secure_cookie

LOGGER = logging.getLogger('script_server.auth.OAuthTokenManager')


class OAuthTokenManager:
    def __init__(self, enabled, fetch_token_callback) -> None:
        self._refresh_tokens = {}  # type: Dict[str, str]
        self._pending_access_tokens = {}  # type: Dict[str, OAuthTokenResponse]
        self._scheduler = None

        self._enabled = enabled
        self._fetch_token_callback = fetch_token_callback

    def update_tokens(self, token_response: OAuthTokenResponse, username, request_handler):
        if not self._enabled:
            return

        request_handler.set_secure_cookie('token', token_response.access_token)

        if token_response.should_refresh():
            refresh_token = token_response.refresh_token

            if self._refresh_tokens.get(username) != refresh_token:
                self._refresh_tokens[username] = refresh_token
                self._schedule_token_refresh(username, refresh_token, token_response.resolve_next_refresh_datetime())

            request_handler.set_secure_cookie('token_details', token_response.serialize_details())

    def can_restore_state(self, request_handler):
        if not self._enabled:
            return False

        token_response = self._restore_token_response_from_cookies(request_handler)
        if token_response is None:
            return False

        if token_response.should_refresh() and token_response.is_refresh_expired():
            return False

        return True

    async def synchronize_user_tokens(self, user, request_handler):
        user_access_token = get_secure_cookie(request_handler, 'token')
        if not self._enabled:
            return user_access_token

        if user in self._pending_access_tokens:
            token_response = self._pending_access_tokens[user]
            if can_write_secure_cookie(request_handler):
                LOGGER.info('Pending access token is available for ' + user + '. Replacing active token')
                del self._pending_access_tokens[user]
                self.update_tokens(token_response, user, request_handler)
            else:
                LOGGER.info('Pending access token is available for ' + user
                            + ', using it without replacing (called from websocket)')

            return token_response.access_token

        if user not in self._refresh_tokens:
            token_details = get_secure_cookie(request_handler, 'token_details')
            if token_details is not None:
                token_response = OAuthTokenResponse.deserialize(user_access_token, token_details)

                if token_response.should_refresh():
                    if token_response.is_refresh_expired():
                        LOGGER.warning(f'Refresh token expired for user {user}. Logging out')

                        return None

                    LOGGER.info(f'Restoring refresh token for user {user} after restart')

                    if token_response.is_access_expired():
                        LOGGER.info(f'Access token expired for user {user}. Requesting a new one')

                        await self._refresh_token(user, token_response.refresh_token, force=True)

                        if user not in self._pending_access_tokens:
                            LOGGER.warning(f'Failed to refresh token for user {user}. Logging out')
                            return None
                        else:
                            token_response = self._pending_access_tokens[user]
                            del self._pending_access_tokens[user]
                            return token_response.access_token

                    else:
                        self._refresh_tokens[user] = token_response.refresh_token
                        self._schedule_token_refresh(
                            user,
                            token_response.refresh_token,
                            token_response.resolve_next_refresh_datetime())

        return user_access_token

    def remove_user(self, username):
        if username in self._refresh_tokens:
            del self._refresh_tokens[username]

        if username in self._pending_access_tokens:
            del self._pending_access_tokens[username]

    def _schedule_token_refresh(self, username, refresh_token, next_refresh_datetime):
        if not self._scheduler:
            self.scheduler = Scheduler()

        if (next_refresh_datetime - datetime.datetime.now()) < datetime.timedelta(seconds=30):
            next_refresh_datetime_adjusted = next_refresh_datetime
        elif (next_refresh_datetime - datetime.datetime.now()) < datetime.timedelta(minutes=2):
            next_refresh_datetime_adjusted = next_refresh_datetime - datetime.timedelta(seconds=10)
        else:
            next_refresh_datetime_adjusted = next_refresh_datetime - datetime.timedelta(minutes=1)

        self.scheduler.schedule(
            next_refresh_datetime_adjusted,
            tornado.ioloop.IOLoop.current().add_callback,
            (self._refresh_token, username, refresh_token))

    async def _refresh_token(self, username, refresh_token, force=False):
        if not force:
            if (username not in self._refresh_tokens) or (self._refresh_tokens[username] != refresh_token):
                return

        token_response = await self._fetch_token_callback(refresh_token, username)

        if token_response is None:
            return

        LOGGER.info(f'Refreshed token for {username}')

        self._refresh_tokens[username] = token_response.refresh_token
        self._pending_access_tokens[username] = token_response

        if token_response.should_refresh():
            self._schedule_token_refresh(
                username,
                token_response.refresh_token,
                token_response.resolve_next_refresh_datetime())

    @staticmethod
    def _restore_token_response_from_cookies(request_handler) -> Optional[OAuthTokenResponse]:
        user_access_token = get_secure_cookie(request_handler, 'token')
        if not user_access_token:
            return None

        token_details = get_secure_cookie(request_handler, 'token_details')
        if token_details is None:
            return None

        return OAuthTokenResponse.deserialize(user_access_token, token_details)

    def logout(self, user, request_handler):
        request_handler.clear_cookie('token')
        request_handler.clear_cookie('token_details')
