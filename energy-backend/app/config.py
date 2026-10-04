import os
from io import StringIO
from pathlib import Path
from dotenv import load_dotenv
BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
env_file = ROOT / ".env"
if env_file.exists():
    lines = [line.replace("$env:","",1) if line.lstrip().startswith("$env:") else line for line in env_file.read_text(encoding="utf-8-sig").splitlines()]
    load_dotenv(stream=StringIO("\n".join(lines)),override=False)
DATASET_PATH = Path(os.getenv("DATASET_PATH",str(ROOT/"energydata_complete.csv")))
MODEL_DIR = Path(os.getenv("MODEL_DIR",str(BACKEND/"models")))
RUNTIME_DIR = Path(os.getenv("RUNTIME_DIR",str(BACKEND/"runtime")))

def jwt_secret():
    value = os.getenv("JWT_SECRET_KEY","").strip()
    if value:
        if len(value)<32:
            raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")
        return value
    if os.getenv("APP_ENV")=="production":
        raise RuntimeError("Set JWT_SECRET_KEY for production")
    import secrets
    RUNTIME_DIR.mkdir(parents=True,exist_ok=True)
    path = RUNTIME_DIR/".jwt-secret"
    if not path.exists():
        try:
            with path.open("x",encoding="utf-8") as stream:
                stream.write(secrets.token_urlsafe(48))
        except FileExistsError:
            pass
    return path.read_text(encoding="utf-8").strip()
