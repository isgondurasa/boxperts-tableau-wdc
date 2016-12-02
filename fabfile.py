import os
import logging
import settings

from fabric.context_managers import cd, lcd
from fabric.api import (run,
                        env,
                        task,
                        local,
                        settings as fabriq_settings)
from fabric.decorators import hosts

HOST = "root@185.143.173.48"
HOST_PATH = "~/wdc"

@hosts(HOST)
def deploy(branch="master", arch_name="app.tar.bz2"):
    """
    deploy a wdc application
    """

    local('git archive --format="tar" "{}" | bzip2 > {}'.format(branch, arch_name))

    remote_path = "{}:{}/".format(HOST, HOST_PATH)
    local('scp {} {}/'.format(arch_name, remote_path))
    local('scp {} {}/'.format("docker-compose.yml", remote_path))
    local('scp {} {}/'.format("Dockerfile", remote_path))
    local('scp {} {}/'.format("web.env", remote_path))
    local('scp {} {}/'.format("requirements.txt", remote_path))
    with cd ('wdc'):
        run("docker-compose down")
        run("docker-compose build")
        run("docker-compose up --force-recreate -d")
