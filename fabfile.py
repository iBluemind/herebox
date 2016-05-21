from fabric.api import *

HEREBOX_AWS_EC2_01 = '52.79.141.111'
HEREBOX_AWS_EC2_02 = '52.79.175.144'

PROJECT_DIR = '/var/www/herebox'
APP_DIR = '%s/app' % PROJECT_DIR

env.user = 'ubuntu'
env.hosts = [HEREBOX_AWS_EC2_01, HEREBOX_AWS_EC2_02]


def pack():
    local('git push origin master', capture=False)


def deploy():
    with settings(warn_only=True):
        with cd(APP_DIR):
            run('./deploy.sh')

