"""Windows-friendly inference entry point."""
import os
from app import config

if __name__=="__main__":
    port=int(os.getenv("PORT","5000"))
    print(f"Starting EnerGenAI at http://127.0.0.1:{port}",flush=True)
    print("Loading scientific libraries, dataset and models. Keep this terminal open; wait for 'Application startup complete'.",flush=True)
    try:
        import uvicorn
        uvicorn.run("app.main:app",host="127.0.0.1",port=port)
    except KeyboardInterrupt:
        print("\nStartup was interrupted (Ctrl+C/terminal stop). Run this command again and allow loading to finish.",flush=True)
        raise SystemExit(130) from None
