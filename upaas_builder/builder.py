# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

import lya

from upaas_builder.storage.exceptions import InvalidStorageConfiguration


log = logging.getLogger(__name__)


class Builder(object):

    def __init__(self, config_path):
        """
        :param config_path: Path to builder configuration.
        """
        self.config = lya.AttrDict.from_yaml(config_path)
        self.storage = self.find_storage_handler()

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
            raise InvalidStorageConfiguration
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
        pass
