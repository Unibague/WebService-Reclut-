#!/bin/sh
set -e

# ./cache se monta como bind mount (ver docker-compose.yml), lo que
# sobrescribe el chown hecho en build time (Dockerfile). Se repara en
# cada arranque para que Apache (www-data) siempre pueda escribir ahí.
mkdir -p /var/www/html/cache
chown -R www-data:www-data /var/www/html/cache
chmod -R 775 /var/www/html/cache

exec "$@"
