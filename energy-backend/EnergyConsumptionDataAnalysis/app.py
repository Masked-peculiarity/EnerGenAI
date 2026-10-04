"""Compatibility launcher for the former backend startup directory."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import app,create_app

if __name__=="__main__":
    import os
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=int(os.getenv("PORT","5000")))
