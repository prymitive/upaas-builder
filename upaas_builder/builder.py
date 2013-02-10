# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import logging

import lya

import plumbum

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
            'paths': [{'name': 'workdir', 'type': 'string'}],
            'storage': [{'name': 'handler', 'type': 'string'}],
            'bootstrap': [],
            'commands': [
                {'name': 'install', 'type': 'string'},
                {'name': 'uninstall', 'type': 'string'}
            ],
        }
        for (key, options) in required.items():
            if not cfg.get(key):
                log.error(u"Section '%s' is missing from '%s'" % (key,
                                                                  config_path))
                raise exceptions.InvalidConfiguration
            for option in options:
                if not cfg[key].get(option['name']):
                    log.error(u"Option '%s' is missing from section '%s' in "
                              u"'%s'" % (option['name'], key, config_path))
                    raise exceptions.InvalidConfiguration
                value = cfg[key][option['name']]
                if option['type'] == 'integer':
                    try:
                        int(value)
                    except ValueError:
                        log.error(u"Option '%s' from section '%s' in '%s' must "
                                  u"be an integer" % (option['name'], key,
                                                      config_path))
                        raise exceptions.InvalidConfiguration

        return cfg

    def find_storage_handler(self):
        """
        Will try to find storage handler class user has set in configuration,
        create instance of it and return that instance.
        """
        storage_handler = None
        name = self.config.storage.handler
        storage_module = ".".join(name.split('.')[0:len(name.split('.')) - 1])
        storage_class = name.split('.')[len(name.split('.')) - 1]
        try:
            exec("from %s import %s as storage_handler" % (
                storage_module, storage_class))
        except ImportError:
            log.error(u"Storage handler '%s' could not be "
                      u"loaded" % self.config.storage.handler)
            raise exceptions.InvalidConfiguration
        else:
            return storage_handler(self.config.storage.settings)

    def build_package(self, force_fresh=False):
        """
        Build a package

        :param force_fresh: Force fresh package built using empty system image.
        """
        pass

    def bootstrap_os(self):
        """
        Bootstrap base os image.
        """
        log.info(u"Bootstrapping os image using")
        bash = plumbum.local("bash")
        for cmd in self.config.bootstrap:
            plumbum.cmd.sudo[bash["-c", "'%s'" % cmd]]
