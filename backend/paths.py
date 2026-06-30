from pathlib import Path

cache = Path("cache") #Mount-auto_generate
config = Path("config") #Mount-auto_generate

config.mkdir(parents=True, exist_ok=True)
Path(cache/"admin").mkdir(parents=True, exist_ok=True)
Path(cache/"videos").mkdir(parents=True, exist_ok=True)
Path(cache/"playlists").mkdir(parents=True, exist_ok=True)

db_path = "sqlite:///config/db.db"
config_json = config / "config.json"