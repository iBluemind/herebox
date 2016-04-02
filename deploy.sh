#!/bin/bash

UWSGI_PATH=/usr/local/bin/uwsgi
ROOT_DIR=/var/areumdaun_api

/bin/chown -R www-data:www-data $ROOT_DIR
$UWSGI_PATH $ROOT_DIR/app/uwsgi_config.ini

