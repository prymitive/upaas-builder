# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas import config


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
            "env": config.DictEntry(value_type=unicode),
            "commands": config.ScriptEntry(required=True),
        },
        "commands": {
            "timelimit": config.IntegerEntry(required=True),
            "install": {
                "env": config.DictEntry(value_type=unicode),
                "cmd": config.StringEntry(required=True),
            },
            "uninstall": {
                "env": config.DictEntry(value_type=unicode),
                "cmd": config.StringEntry(required=True),
            },
        },
        "interpreters": config.WildcardEntry(),
    }
