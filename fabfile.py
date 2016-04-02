from fabric.api import *
from contextlib import contextmanager as _contextmanager

ARITAUM_SERVER_01 = '125.209.199.163'
ARITAUM_SERVER_02 = '125.209.199.239'

UWSGI_PATH = '/usr/local/bin/uwsgi'
PROJECT_DIR = '/var/areumdaun_api'
APP_DIR = '%s/app' % PROJECT_DIR

env.user = 'root'
env.hosts = [ARITAUM_SERVER_01, ARITAUM_SERVER_02]
env.directory = '%s/venv' % PROJECT_DIR
env.activate = '%s/bin/activate' % env.directory


@_contextmanager
def virtualenv():
    with cd(env.directory):
        with prefix(env.activate):
            yield


def pack():
    local('git push origin master', capture=False)


def install_new_package():
    with cd(APP_DIR):
        with virtualenv():
            run('pip install -r requirements.pip')


def deploy():
    with settings(warn_only=True):
        with cd(APP_DIR):
            run('git pull origin master')

            if run('pgrep "supervisor"'):
                sudo('pkill -f uwsgi')

            else:
                execute(install_new_package)
                with virtualenv():
                    run('%s %s/app/uwsgi_config.ini' % (UWSGI_PATH, APP_DIR))

