#!/bin/bash

docker stop script-server-ldap
docker rm script-server-ldap

set -e

docker run \
--name script-server-ldap \
--env LDAP_ORGANISATION="Script server" \
--env LDAP_DOMAIN="script-server.net" \
--env LDAP_ADMIN_PASSWORD="admin_passw" \
--volume "$PWD"/bootstrap.ldif:/container/service/slapd/assets/config/bootstrap/ldif/50-bootstrap.ldif \
--detach \
osixia/openldap:1.4.0 \
--copy-service \
--loglevel debug