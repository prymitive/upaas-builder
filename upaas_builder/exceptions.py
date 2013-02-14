# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


class InvalidConfiguration(Exception):
    """
    Raised if upaas-builder configuration is invalid.
    """
    pass


class OSBootstrapError(Exception):
    """
    Raised in case of errors during os image bootstraping.
    """
    pass


class PackageSystemError(Exception):
    """
    Raised in case of system errors during package build. This does not cover
    errors caused by package configuration or any commands executed by package
    itself, only errors independent from package (os bootstrap error for
    example)
    """
    pass


class PackageUserError(Exception):
    """
    Raised when executing package specific actions.
    """
    pass
