import os
from pathlib import Path
print(os.getenv("TELEGRAM_TOKEN"))


print("Working dir:", Path.cwd())
print(".env exists:", Path(".env").exists())