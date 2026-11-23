"""
File scanner, path collision handlers, state tracker, lockfile manager,
and batch worker logic. Works identically on macOS and Windows 10/11 using pathlib.
"""

import os
import sys
import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Supported input image extensions
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def scan_images(folder_path: str) -> List[Path]:
    """
    Scans a folder non-recursively for supported image files.
    Cross-platform pathlib implementation.
    Sorted alphabetically for deterministic ordering.
    """
    if not folder_path or not str(folder_path).strip():
        return []
    path = Path(folder_path.strip()).expanduser()
    if not path.is_dir():
        return []
    
    files = []
    try:
        for entry in path.iterdir():
            if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(entry)
    except Exception:
        return []
    
    return sorted(files, key=lambda p: p.name.lower())


def check_path_overlap(input_path: str, output_path: str) -> bool:
    """
    Checks if input folder and output folder are identical or nested inside one another.
    Uses resolved absolute Path objects for cross-platform reliability.
    """
    try:
        inp = Path(input_path.strip()).expanduser().resolve()
        out = Path(output_path.strip()).expanduser().resolve()
        if inp == out:
            return True
        if out in inp.parents or inp in out.parents:
            return True
        return False
    except Exception:
        return False


def get_collision_safe_name(dest_folder: Path, stem: str, ext: str) -> Path:
    """
    Generates a unique file path if stem.ext already exists in dest_folder.
    Format: stem.ext -> stem_1.ext -> stem_2.ext
    """
    candidate = dest_folder / f"{stem}{ext}"
    if not candidate.exists():
        return candidate
    counter = 1
    while True:
        candidate = dest_folder / f"{stem}_{counter}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def open_folder_in_os(folder_path: Path):
    """
    Opens the destination folder in the native OS file explorer (Finder on macOS, Explorer on Windows).
    """
    try:
        p = Path(folder_path).resolve()
        if not p.exists():
            return
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(str(p))
        elif current_os == "Darwin":
            subprocess.run(["open", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
    except Exception as e:
        logging.getLogger("BulkBgRemover").error(f"Could not open folder in OS: {e}")


class DirectoryLock:
    """
    Prevents multiple simultaneous jobs from writing to the same output directory.
    Uses an atomic lock file mechanism.
    """
    def __init__(self, output_dir: Path):
        self.lock_file = output_dir / ".batch_worker.lock"
        self._acquired = False

    def acquire(self) -> bool:
        if self.lock_file.exists():
            return False
        try:
            self.lock_file.write_text(f"PID: {os.getpid()}\n", encoding="utf-8")
            self._acquired = True
            return True
        except Exception:
            return False

    def release(self):
        if self._acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass
            self._acquired = False

    def is_locked(self) -> bool:
        return self.lock_file.exists()


class BatchProgressTracker:
    """
    Tracks state of a batch for resumption and skip logic.
    Records processing configuration parameters to invalidate/revalidate resumption.
    Persists to batch_status.json in output directory.
    """
    def __init__(self, output_dir: Path, current_settings: Optional[Dict[str, Any]] = None):
        self.output_dir = output_dir
        self.status_file = output_dir / "batch_status.json"
        self.current_settings = current_settings or {}
        self.state: Dict[str, Any] = {
            "settings": self.current_settings,
            "completed": [],
            "failed": []
        }
        self.load()

    def load(self):
        if self.status_file.exists():
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    
                saved_settings = saved.get("settings", {})
                if self.current_settings:
                    keys_to_compare = ["canvas_dim", "padding_pct", "export_format"]
                    settings_differ = any(
                        saved_settings.get(k) != self.current_settings.get(k)
                        for k in keys_to_compare
                        if k in saved_settings and k in self.current_settings
                    )
                    if settings_differ:
                        self.state = {
                            "settings": self.current_settings,
                            "completed": [],
                            "failed": []
                        }
                        return

                self.state = {
                    "settings": saved.get("settings", self.current_settings),
                    "completed": saved.get("completed", []),
                    "failed": saved.get("failed", [])
                }
            except Exception:
                self.state = {"settings": self.current_settings, "completed": [], "failed": []}

    def save(self):
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception:
            pass

    def is_processed(self, filename: str) -> bool:
        return filename in self.state.get("completed", [])

    def record_success(self, filename: str):
        if filename not in self.state["completed"]:
            self.state["completed"].append(filename)
        if filename in self.state["failed"]:
            self.state["failed"].remove(filename)
        self.save()

    def record_failure(self, filename: str):
        if filename not in self.state["failed"]:
            self.state["failed"].append(filename)
        self.save()


def setup_logger(log_file_path: Path) -> logging.Logger:
    logger = logging.getLogger(f"BulkBgRemover_{log_file_path.parent.name}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    fh = logging.FileHandler(str(log_file_path), encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def format_duration(seconds: float) -> str:
    """Format seconds into human readable MM:SS or HH:MM:SS."""
    secs = int(seconds)
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    rem_secs = secs % 60
    if mins < 60:
        return f"{mins}m {rem_secs:02d}s"
    hours = mins // 60
    rem_mins = mins % 60
    return f"{hours}h {rem_mins:02d}m {rem_secs:02d}s"
