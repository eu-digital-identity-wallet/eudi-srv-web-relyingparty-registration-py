import os

class ConfDataBase:

    DATABASE = {
        'host': os.getenv("DB_HOST", "localhost"),
        'port': int(os.getenv("DB_PORT", 3306)),
        'user': os.getenv("DB_USER", "root"),
        'password': os.getenv("DB_PASSWORD", "123456"),
        'database': os.getenv("DB_NAME","relyingparty_reg")
    }