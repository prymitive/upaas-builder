# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import platform


def distro_name():
    return platform.dist()[0]


def distro_version():
    return platform.dist()[1]


def distro_codename():
    return platform.dist()[2]


def distro_image_filename():
    #FIXME extension is hardcoded to tar.gz, make image compression configurable
    return u"%s-%s.tar.gz" % (distro_name(), distro_version())
