from __future__ import annotations

import datetime
import json
from typing import Optional


def _calc_expires_at(expires_in, response_datetime):
    if expires_in is None:
        return None

    return response_datetime + datetime.timedelta(seconds=expires_in)


def _date_to_string(expires_at: datetime) -> Optional[str]:
    if expires_at is None:
        return None

    return expires_at.isoformat()


def _string_to_date(expires_at: datetime) -> Optional[datetime.datetime]:
    if expires_at is None:
        return None

    return datetime.datetime.fromisoformat(expires_at)


class OAuthTokenResponse:

    def __init__(self, access_token, access_expires_at, refresh_token, refresh_expires_at) -> None:
        self.access_token = access_token
        self.access_expires_at = access_expires_at
        self.refresh_token = refresh_token
        self.refresh_expires_at = refresh_expires_at

    @classmethod
    def create(cls, response_values, response_datetime) -> OAuthTokenResponse:
        return OAuthTokenResponse(
            response_values.get('access_token'),
            _calc_expires_at(response_values.get('expires_in'), response_datetime),
            response_values.get('refresh_token'),
            _calc_expires_at(response_values.get('refresh_expires_in'), response_datetime))

    def should_refresh(self):
        return self.refresh_token and self.access_expires_at

    def get_refresh_expires_at(self):
        return self.refresh_expires_at

    def get_access_expires_at(self):
        return self.access_expires_at

    def resolve_next_refresh_datetime(self):
        if not self.should_refresh():
            raise Exception('Cannot resolve expires at, for non-refreshable tokens')

        if self.access_expires_at:
            return self.access_expires_at

        if self.refresh_expires_at:
            return self.refresh_expires_at

        return datetime.datetime.now() + datetime.timedelta(days=1)

    def serialize_details(self):
        return json.dumps({
            'refresh_token': self.refresh_token,
            'access_expires_at': _date_to_string(self.access_expires_at),
            'refresh_expires_at': _date_to_string(self.refresh_expires_at)
        })

    @classmethod
    def deserialize(cls, access_token, serialized) -> OAuthTokenResponse:
        deserialized = json.loads(serialized)

        return OAuthTokenResponse(
            access_token,
            _string_to_date(deserialized['access_expires_at']),
            deserialized.get('refresh_token'),
            _string_to_date(deserialized['refresh_expires_at'])
        )

    def is_refresh_expired(self):
        expires_at = self.get_refresh_expires_at()
        if expires_at is None:
            return False

        return expires_at <= datetime.datetime.now()

    def is_access_expired(self):
        expires_at = self.get_access_expires_at()
        if expires_at is None:
            return False

        return expires_at <= datetime.datetime.now()
