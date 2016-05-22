#!/bin/bash

GIT_PATH=/usr/bin/git
PKILL_PATH=/usr/bin/pkill
ROOT_DIR=/var/www/herebox
VENV_PATH=$ROOT_DIR/venv
UWSGI_PATH=$VENV_PATH/bin/uwsgi
ACTIVATE_PATH=$VENV_PATH/bin/activate

function build_forge_min_js {
    local forge_min_js="$ROOT_DIR/app/hereboxweb/static/libs/forge/js/forge.min.js"
    if [ -f "$forge_min_js" ]
    then
        echo "forge_min_js is existed."
    else
        cd "$ROOT_DIR/app/hereboxweb/static/libs/forge"
        npm install
        npm run minify
    fi
}

cd $ROOT_DIR/app
$GIT_PATH pull origin master

build_forge_min_js

/bin/chown -R www-data:www-data $ROOT_DIR

$PKILL_PATH -f -INT uwsgi
source $ACTIVATE_PATH
$UWSGI_PATH $ROOT_DIR/app/uwsgi_config.ini

