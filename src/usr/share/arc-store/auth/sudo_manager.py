"""
auth/sudo_manager.py — the only sanctioned way any part of Arc Store talks
to root. No privileged operation ever calls subprocess with a bare "sudo",
and the password never appears on a command line (invisible to `ps aux`)
or touches disk.

SudoManager is a singleton that authenticates the password once and then
lets you run any number of commands as root without re-entering it. The
password is handed to `sudo` through a private named pipe (FIFO), read via
sudo's SUDO_ASKPASS mechanism.
"""

import os
import subprocess
import tempfile
import threading
import atexit
from typing import Optional


class SudoManager:
    _instance: Optional["SudoManager"] = None

    @classmethod
    def get_instance(cls) -> "SudoManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.user_password = None
        self._running = True

        askpass_tf = tempfile.NamedTemporaryFile(delete=False, prefix="arc-store-askpass-")
        self.askpass_script = askpass_tf.name
        askpass_tf.close()

        wrapper_tf = tempfile.NamedTemporaryFile(delete=False, prefix="arc-store-sudo-")
        self.wrapper_path = wrapper_tf.name
        wrapper_tf.close()

        self.fifo_dir = tempfile.mkdtemp(prefix="arc-store-pipe-")
        self.fifo_path = os.path.join(self.fifo_dir, "password_pipe")
        os.mkfifo(self.fifo_path, 0o600)

        self._setup_scripts()

        self._feed_condition = threading.Condition()
        self._feeds_allowed = 0
        self.feeder_thread = threading.Thread(target=self._feed_pipe_loop, daemon=True)
        self.feeder_thread.start()
        atexit.register(self.cleanup)

    def _setup_scripts(self):
        with open(self.askpass_script, "w") as f:
            f.write(f'#!/bin/sh\ncat "{self.fifo_path}"\n')
        os.chmod(self.askpass_script, 0o700)
        with open(self.wrapper_path, "w") as f:
            f.write("#!/bin/sh\n"
                    f"export SUDO_ASKPASS='{self.askpass_script}'\n"
                    'exec sudo -A "$@"\n')
        os.chmod(self.wrapper_path, 0o700)

    def _feed_pipe_loop(self):
        """Background thread: writes the password to the FIFO only when
        someone has raised _feeds_allowed. Opening the FIFO for writing
        blocks until sudo -A (via askpass_script) opens it for reading —
        both sides meet exactly when sudo actually asks for the password."""
        while self._running:
            with self._feed_condition:
                self._feed_condition.wait_for(lambda: self._feeds_allowed > 0 or not self._running)
            if not self._running:
                break
            if self.user_password:
                try:
                    fd = os.open(self.fifo_path, os.O_WRONLY)
                    with os.fdopen(fd, "w") as f:
                        f.write(str(self.user_password) + "\n")
                    with self._feed_condition:
                        if self._feeds_allowed > 0:
                            self._feeds_allowed -= 1
                except OSError:
                    pass
            else:
                with self._feed_condition:
                    if self._feeds_allowed > 0:
                        self._feeds_allowed -= 1

    def validate_password(self, password: str) -> bool:
        """Immediate validation via `sudo -S -v` (password on stdin) —
        doesn't run anything privileged yet. Lets a dialog show 'wrong
        password' before it even closes."""
        if not password:
            return False
        subprocess.run(["sudo", "-k"], check=False)
        result = subprocess.run(
            ["sudo", "-S", "-v"], input=password + "\n",
            capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"},
        )
        return result.returncode == 0

    def set_password(self, password: str):
        self.user_password = password

    def get_env(self) -> dict:
        """A plain environment copy for subprocess calls. The password
        never goes in here — it only ever flows through the FIFO."""
        return os.environ.copy()

    def run_privileged(self, cmd: list, **kwargs):
        """cmd e.g. ['pacman', '-S', '--noconfirm', 'package-name']."""
        if not self.user_password:
            raise ValueError("No password set — call validate_password() + set_password() first")
        with self._feed_condition:
            self._feeds_allowed += 1
            self._feed_condition.notify_all()
        try:
            return subprocess.run([self.wrapper_path] + cmd, **kwargs)
        finally:
            self._drain_pipe()

    def start_privileged_session(self):
        """Open the gate for many reads at once — wrap a block of code that
        itself launches several root subprocesses."""
        if not self.user_password:
            return
        with self._feed_condition:
            self._feeds_allowed = 1000
            self._feed_condition.notify_all()

    def stop_privileged_session(self):
        with self._feed_condition:
            self._feeds_allowed = 0
        self._drain_pipe()

    def _drain_pipe(self):
        with self._feed_condition:
            remaining = self._feeds_allowed
        if remaining > 0:
            try:
                fd = os.open(self.fifo_path, os.O_RDONLY | os.O_NONBLOCK)
                os.read(fd, 1024)
                os.close(fd)
            except Exception:
                pass

    def forget_password(self):
        """Call after EVERY finished privileged operation."""
        self.user_password = None
        subprocess.run(["sudo", "-k"], check=False)

    def cleanup(self):
        self._running = False
        self.forget_password()
        for p in (self.askpass_script, self.wrapper_path, self.fifo_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(self.fifo_dir)
        except OSError:
            pass


def get_sudo_manager() -> SudoManager:
    return SudoManager.get_instance()
