from typing import Callable

if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_DIR))


from medlogserver.config import Config

config = Config()


import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.app:app", host="0.0.0.0", log_level="info")
