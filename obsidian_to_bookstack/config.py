import os

import toml
from dotenv import load_dotenv

from .sqllite import DatabaseFunctions as dbf


def load_env(env: str):
    """Load environment vars"""

    if env:
        ENV_PATH = os.path.expanduser(env)
    else:
        loaded_env = dbf.select_env()
        ENV_PATH = loaded_env or ".env"

    try:
        dbf.update_env(ENV_PATH)
        if os.path.exists(ENV_PATH):
            load_dotenv(ENV_PATH)
    except FileNotFoundError:
        print(f"Couldn't find file: {ENV_PATH}")
    except Exception as e:
        print(f"Error loading environment variables: {e}")


def load_toml(conf_path: str):
    """Try to load config"""

    if not conf_path:
        if conf := dbf.select_config():
            conf_path = conf
            dbf.update_config(conf_path)
        else:
            USER = os.environ["USER"]
            path = f"/home/{USER}/.config/obsidian_to_bookstack"
            conf_path = os.path.join(path, "conf.toml")
            dbf.update_config(conf_path)

    try:
        with open(conf_path, "r") as t:
            return toml.load(t)
    except:
        print("Couldn't load 'conf.toml'")
