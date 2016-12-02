import os
import logging
import settings

from fabric.context_managers import cs, lcd
from fabriq.api import (run,
                        env,
                        task,
                        local,
                        settings as fabriq_settings)
from fabric.decorators import hosts

HOST = "root@185.143.173.48"
HOOST_PATH = "~/wdc"

def deploy(branch="master", arch_name="app.tar.bz2"):
    """
    deploy a wdc application
    """

    local("git archive --format="tar" "{}" | bzip > {}".format(branch, arch_name))

    remote_path = "{}:{}/".format(HOST, HOST_PATH)
    local('scp {} {}/'.format(arch_name, remote_path))
