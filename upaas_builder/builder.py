# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import tempfile
import shutil
import logging

from upaas import distro

from upaas import commands
from upaas import tar
from upaas import config

from upaas_builder import exceptions

log = logging.getLogger(__name__)


class BuilderConfig(config.Config):

    schema = {
        "paths": {
            "workdir": config.FSPathEntry(required=True, must_exist=True),
            },
        "storage": {
            "handler": config.StringEntry(required=True),
            "settings": {
                "dir": config.FSPathEntry(required=True, must_exist=True),
                }
        },
        "bootstrap": {
            "timelimit": config.IntegerEntry(required=True),
            "env": config.ListEntry(unicode),
            "commands": config.ScriptEntry(required=True),
            },
        "commands": {
            "install": config.StringEntry(required=True),
            "uninstall": config.StringEntry(required=True),
            }
        #TODO interpreters?
    }


class Builder(object):

    def __init__(self, config_path):
        """
        :param config_path: Path to builder configuration.
        """
        self.config = BuilderConfig.from_file(config_path)
        self.storage = self.find_storage_handler()

    def find_storage_handler(self):
        """
        Will try to find storage handler class user has set in configuration,
        create instance of it and return that instance.
        """
        storage_handler = None
        name = self.config.storage.handler
        storage_module = ".".join(name.split(".")[0:len(name.split(".")) - 1])
        storage_class = name.split(".")[len(name.split(".")) - 1]
        try:
            exec("from %s import %s as storage_handler" % (
                storage_module, storage_class))
        except ImportError:
            log.error(u"Storage handler '%s' could not be "
                      u"loaded" % self.config.storage.handler)
            raise exceptions.InvalidConfiguration
        else:
            try:
                return storage_handler(self.config.storage.settings.dump())
            except config.ConfigurationError:
                log.error(u"Storage handler failed to initialize with given "
                          u"configuration")
                raise exceptions.InvalidConfiguration

    def build_package(self, force_fresh=False):
        """
        Build a package

        :param force_fresh: Force fresh package built using empty system image.
        """
        def _cleanup(directory):
            log.info(u"Removing directory '%s'" % directory)
            shutil.rmtree(directory)

        if not self.has_valid_os_image():
            try:
                self.bootstrap_os()
            except exceptions.OSBootstrapError:
                log.error(u"Error during os bootstrap, aborting")
                raise exceptions.PackageSystemError

        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_package_")

        #TODO right now we always build fresh package


    def has_valid_os_image(self):
        """
        Check if os image exists and is fresh enough.
        """
        if not self.storage.exists(distro.distro_image_filename()):
            return False

        #TODO check os image mtime
        return True

    def bootstrap_os(self):
        """
        Bootstrap base os image.
        """
        def _cleanup(directory):
            log.info(u"Removing directory '%s'" % directory)
            shutil.rmtree(directory)

        log.info(u"Bootstrapping os image using")

        directory = tempfile.mkdtemp(dir=self.config.paths.workdir,
                                     prefix="upaas_bootstrap_")
        log.debug(u"Created temporary directory for bootstrap at "
                  u"'%s'" % directory)

        cmd = self.config.bootstrap.commands.replace("%workdir%", directory)
        try:
            commands.execute(cmd, timeout=self.config.bootstrap.timelimit,
                             cwd=directory,
                             env=self.config.bootstrap.env or [])
        except commands.CommandTimeout:
            log.error(u"Bootstrap was taking too long and it was killed")
            _cleanup(directory)
            raise exceptions.OSBootstrapError
        except commands.CommandFailed:
            log.error(u"Bootstrap command failed")
            _cleanup(directory)
            raise exceptions.OSBootstrapError
        log.info(u"Bootstrap done, packing image")

        archive_path = os.path.join(directory, "image.tar.gz")
        if not tar.pack_tar(directory, archive_path,
                            timeout=self.config.bootstrap.timelimit):
            _cleanup(directory)
            raise exceptions.OSBootstrapError
        else:
            log.info(u"Image packed, uploading")
            self.storage.put(archive_path, distro.distro_image_filename())

        log.info(u"Image uploaded")
        _cleanup(directory)
        log.info(u"All done")
