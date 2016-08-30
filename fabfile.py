from fabric.api import *

HEREBOX_AWS_EC2_01 = '172.31.10.181'  # Stopped
HEREBOX_AWS_EC2_02 = '172.31.10.182'  # Running

PROJECT_DIR = '/var/www/herebox'
APP_DIR = '%s/app' % PROJECT_DIR

env.user = 'ubuntu'
env.hosts = [HEREBOX_AWS_EC2_01, HEREBOX_AWS_EC2_02]
env.key_filename = '/Users/Urang/herebox-web.pem'


def pack():
    local('git push origin master', capture=False)


def deploy():
    with settings(warn_only=True):
        with cd(APP_DIR):
            run('sudo ./deploy.sh')

