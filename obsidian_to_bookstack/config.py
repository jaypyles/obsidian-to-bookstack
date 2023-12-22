import os

import toml


def load_toml():
    """Try to load config"""
    cwd = os.getcwd()
    conf_path = os.path.join(cwd, "conf.toml")

    try:
        with open(conf_path, "r") as t:
            return toml.load(t)
    except:
        print("Couldn't load 'conf.toml'")
