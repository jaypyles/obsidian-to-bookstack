import os

import toml


def load_toml():
    """Try to load config"""
    USER = os.environ["USER"]
    path = f"/home/{USER}/.config/obsidian_to_bookstack"
    conf_path = os.path.join(path, "conf.toml")

    try:
        with open(conf_path, "r") as t:
            return toml.load(t)
    except:
        print("Couldn't load 'conf.toml'")
