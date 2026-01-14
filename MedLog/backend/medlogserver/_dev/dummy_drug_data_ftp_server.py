"""
Simple FTP server for that serves the dummy drug data. For testing and dev pipeline purposes only.
"""

import multiprocessing
import signal
import time
import yaml
from pathlib import Path
from typing import Optional, Dict, List
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

CONFIG_DATABASE_FILE = Path(Path(__file__).parent, "ftp_testusers.yaml")
DUMMY_DRUG_DATA_PATH = Path(
    Path(__file__).parent.parent.parent, "provisioning_data/dummy_drugset"
)


class FTPTestServer:
    """A simple FTP server for testing that runs in a subprocess."""

    def __init__(
        self,
        directory: str,
        host: str = "127.0.0.1",
        port: int = 21,
    ):
        """
        Initialize FTP test server.

        Args:
            directory: Directory to serve via FTP
            host: Host address to bind to
            port: Port number to listen on
        """
        self.config_file = Path(CONFIG_DATABASE_FILE)
        self.directory = Path(directory)
        self.host = host
        self.port = port
        self.process: Optional[multiprocessing.Process] = None

        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {self.directory}")

        if not self.config_file.exists():
            raise ValueError(f"Config file does not exist: {self.config_file}")

    def _load_config(self) -> List[Dict[str, str]]:
        """Load user configuration from YAML file."""
        with open(self.config_file, "r") as f:
            config = yaml.safe_load(f)

        if "users" not in config:
            raise ValueError("Config file must contain 'users' key")

        return config["users"]

    @staticmethod
    def _run_server(config_file: str, directory: str, host: str, port: int):
        """
        Run the FTP server (executed in subprocess).

        This method sets up signal handlers to ensure clean shutdown
        when parent process sends KeyboardInterrupt.
        """

        # Handle termination signals gracefully
        def signal_handler(signum, frame):
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Load config
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # Setup authorizer
            authorizer = DummyAuthorizer()

            for user in config["users"]:
                username = user["username"]
                password = user["password"]
                permissions = user.get("permissions", "elradfmw")

                authorizer.add_user(
                    username=username,
                    password=password,
                    homedir=directory,
                    perm=permissions,
                )

            # Setup handler and server
            handler = FTPHandler
            handler.authorizer = authorizer

            server = FTPServer((host, port), handler)

            print(f"FTP server started on {host}:{port}")
            print(f"Serving directory: {directory}")

            # Start serving
            server.serve_forever()

        except KeyboardInterrupt:
            print("\nFTP server shutting down...")
        except Exception as e:
            print(f"FTP server error: {e}")
            raise

    def start(self):
        """Start the FTP server in a subprocess."""
        if self.process and self.process.is_alive():
            raise RuntimeError("Server is already running")

        self.process = multiprocessing.Process(
            target=self._run_server,
            args=(str(self.config_file), str(self.directory), self.host, self.port),
        )

        self.process.start()

        # Give server time to start
        time.sleep(0.5)

        if not self.process.is_alive():
            raise RuntimeError("Server failed to start")

        print(f"FTP server process started (PID: {self.process.pid})")

    def stop(self, timeout: int = 5):
        """
        Stop the FTP server.

        Args:
            timeout: Seconds to wait for graceful shutdown before forcing
        """
        if not self.process:
            return

        if self.process.is_alive():
            print("Stopping FTP server...")
            self.process.terminate()
            self.process.join(timeout=timeout)

            if self.process.is_alive():
                print("Force killing FTP server...")
                self.process.kill()
                self.process.join()

        self.process = None
        print("FTP server stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


if __name__ == "__main__":
    # Create directory to serve
    import sys
    import os

    # Drug data path

    sys.path.insert(0, str(DUMMY_DRUG_DATA_PATH))

    from zip_dummy_drugsets import zip_drugset_directories

    zip_drugset_directories()
    serve_dir = Path(DUMMY_DRUG_DATA_PATH, "zipped")

    # Start server using context manager
    try:
        with FTPTestServer(
            directory=str(serve_dir),
            host="127.0.0.1",
            port=2121,
        ) as server:
            print("\nServer running. Press Ctrl+C to stop...")
            print(f"Connect with: ftp://testuser:testpass@127.0.0.1:2121")

            # Keep running until interrupted
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt in main process")
