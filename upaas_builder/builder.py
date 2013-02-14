# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import tempfile
import shutil
import logging

import lya

from upaas import distro

from upaas.storage.exceptions import InvalidStorageConfiguration
from upaas import commands
from upaas import tar

from upaas_builder import exceptions


log = logging.getLogger(__name__)


class Builder(object):

    def __init__(self, config_path):
        """
        :param config_path: Path to builder configuration.
        """
        self.config = self.validate_configuration(config_path)
        self.storage = self.find_storage_handler()

    def validate_configuration(self, config_path):
        if not os.path.exists(config_path):
            log.error(u"Configuration file not found at '%s'" % config_path)
            raise exceptions.InvalidConfiguration

        log.info(u"Loading configuration from '%s'" % config_path)
        cfg = lya.AttrDict.from_yaml(config_path)

        required = {
            "paths": [{"name": "workdir", "types": [basestring], "path": True}],
            "storage": [{"name": "handler", "types": [basestring]}],
            "bootstrap": [
                {"name": "timelimit", "types": [int]},
                {"name": "commands", "types": [list, basestring]}
            ],
            "commands": [
                {"name": "install", "types": [basestring]},
                {"name": "uninstall", "types": [basestring]}
            ],
        }
        for (key, options) in required.items():
            if not cfg.get(key):
                log.error(u"Section '%s' is missing from '%s'" % (key,
                                                                  config_path))
                raise exceptions.InvalidConfiguration
            for option in options:
                if not cfg[key].get(option["name"]):
                    log.error(u"Option '%s' is missing from section '%s' in "
                              u"'%s'" % (option["name"], key, config_path))
                    raise exceptions.InvalidConfiguration
                value = cfg[key][option["name"]]
                is_valid = "types" not in option
                for vtype in option.get("types", []):
                    if isinstance(value, vtype):
                        is_valid = True
                        break
                if not is_valid:
                    log.error(u"Option '%s' from section '%s' in '%s' must "
                              u"be %s, %s "
                              u"given" % (option["name"], key, config_path,
                                          " or ".join(
                                              repr(t) for t in option["types"]
                                          ), value.__class__.__name__))
                    raise exceptions.InvalidConfiguration
                if "path" in option and not os.path.exists(value):
                    log.error(u"Path '%s' in option '%s' from section '%s' "
                              u"does not exist" % (value, option["name"], key))
                    raise exceptions.InvalidConfiguration
        return cfg

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
                return storage_handler(self.config.storage.settings)
            except InvalidStorageConfiguration:
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

        #FIXME allow for bootstrap command as a single/multiline string
        for cmd in self.config.bootstrap.commands:
            cmd = cmd.replace("%workdir%", directory)
            try:
                commands.execute(cmd, timeout=self.config.bootstrap.timelimit,
                                 cwd=directory,
                                 env=self.config.bootstrap.env or [])
            except commands.CommandTimeoutAlarm:
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
