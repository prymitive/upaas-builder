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


class MetadataConfig(config.Config):

    schema = {
        "os": config.WildcardEntry(),
        "interpreter": {
            "type": config.StringEntry(required=True),
            "versions": config.ListEntry(unicode),
        },
        "repository": {
            "env": config.DictEntry(value_type=unicode),
            "clone": config.ScriptEntry(required=True),
            "update": config.ScriptEntry(required=True),
            "info": config.ScriptEntry(required=True),
            "changelog": config.ScriptEntry(required=True),
        },
        "env": config.DictEntry(value_type=unicode),
        "actions": {
            "setup": {
                "before": config.ScriptEntry(),
                "main": config.ScriptEntry(),
                "after": config.ScriptEntry(),
            }
        }
    }
