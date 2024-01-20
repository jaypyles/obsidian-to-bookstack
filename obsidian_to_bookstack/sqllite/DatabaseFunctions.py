import os
import sqlite3

DATA_PATH = f"/home/{os.environ.get("USER")}/.config/obsidian_to_bookstack/data"

def connect():
    conn = sqlite3.connect(f"{DATA_PATH}/settings.db")
    cursor = conn.cursor()
    return conn, cursor


def make_data_folder():
    if not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)


def create_settings_if_not_exists():
    make_data_folder()
    conn, cursor = connect()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            config_location TEXT,
            env_location TEXT
        );
        """
    )
    conn.close()


def select_config() -> str | None:
    conn, cursor = connect()
    cursor.execute(
        """
        SELECT config_location FROM settings;
        """
    )
    result = cursor.fetchone()
    config = result[0] if result else None

    conn.close()
    return config


def select_env() -> str | None:
    conn, cursor = connect()
    cursor.execute(
        f"""
        SELECT env_location FROM settings;
        """
    )
    result = cursor.fetchone()
    env = result[0] if result else None
    conn.close()
    return env if env else None


def update_config(config: str):
    conn, cursor = connect()
    cursor.execute(
        """
        INSERT OR REPLACE INTO settings (id, config_location, env_location)
        VALUES (
            1,
            ?,
            (SELECT env_location FROM settings WHERE id = 1)
        );
        """,
        (config,),
    )

    conn.commit()
    conn.close()


def update_env(env: str):
    conn, cursor = connect()
    cursor.execute(
        """
        INSERT OR REPLACE INTO settings (id, config_location, env_location)
        VALUES (
            1,
            (SELECT config_location FROM settings WHERE id = 1),
            ?
        );
        """,
        (env,),
    )
    conn.commit()
    conn.close()


def init_db():
    create_settings_if_not_exists()
