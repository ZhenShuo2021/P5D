# Todo: Logging if remote path exists.
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from p5d import app_settings, custom_logger
from p5d.utils import ConfigLoader, normalize_path


class FileSyncer:
    def __init__(
        self,
        config_loader: ConfigLoader,
        logger: logging.Logger,
        rsync_param: dict = {},
    ):
        self.logger = logger
        self.log_dir = config_loader.get_log_dir()
        self.config_loader = config_loader
        self.rsync_param = self.update_param(config_loader.get_custom(), rsync_param)

    def sync_folders(self, src: Any, dst: Any) -> None:
        """Sync folder with rsync.

        If input is None, it will sync all categories with sync_folders_all.
        src is either str or None.
        """
        if not src:
            self.sync_folders_all()
        else:
            src, dst = Path(src), Path(dst)
            if not src.is_dir():
                self.logger.error(f"Syncing file error: local folder '{src}' not exist.")
            if not dst.is_dir():
                self.logger.debug(f"Create nonexisting target folder '{str(self.log_dir)}'.")
                dst.mkdir(parents=True, exist_ok=True)

            log_path = self._log_name(self.log_dir, src)
            self._run_rsync(src, dst, log_path)

    def sync_folders_all(self) -> None:
        combined_paths = self.config_loader.get_combined_paths()
        for key in combined_paths:
            # Not use get method to prevent infinite loop
            if not combined_paths.get(key, {}).get("local_path", {}):
                self.logger.error(
                    f"Local path of '{combined_paths[key]}' not found, continue to prevent infinite loop."
                )
                continue
            self.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])
        log_merger = LogMerger(self.log_dir, self.logger)
        log_merger.merge_logs()

    def _log_name(self, log_dir: Path, src: Path) -> str:
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Creates folder '{log_dir}'")
        return os.path.join(str(log_dir), f"{os.path.basename(src)}{app_settings.LOG_TEMP_EXT}")

    def _run_rsync(self, src: str | Path, dst: str | Path, log_path: str | Path) -> None:
        src = normalize_path(self.add_slash(src))
        dst = normalize_path(self.add_slash(dst))
        if not self.rsync_param:
            command = [
                "rsync",
                "-aq",
                "--ignore-existing",
                "--progress",
                f"--log-file={log_path}",
                src,
                dst,
            ]
        else:
            rsync_options = self.rsync_param.split()
            command = [
                "rsync",
                *rsync_options,
                f"{self.add_slash(src)}/",
                f"{self.add_slash(dst)}/",
            ]
        self.logger.debug(f"Start Syncing '{self.add_slash(src)}' to '{self.add_slash(dst)}'.")
        try:
            # Do not use shell=True
            subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Synchronization failed: {e}")

    def update_param(self, file_input: dict[str, str], cmd_input: dict[str, str]) -> str:
        """Overwrite rsync parameter
        The priority is cmd > file > default
        """
        # file_output = file_input.get("custom", {}).get("rsync", "")
        # combined_string = ",".join(file_output)
        return cmd_input.get("rsync", "") or file_input.get("rsync", "") or ""

    def add_slash(self, path: str | Path) -> str:
        path = rf"{str(path)}\\" if app_settings.USER_OS == "Windows" else f"{str(path)}/"
        return path


class LogMerger:
    def __init__(self, log_dir: Path, logger: logging.Logger):
        self.log_dir = log_dir
        self.logger = logger

    def merge_logs(self) -> None:
        output_file = self.log_dir / Path(
            f"rsync_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        )
        log_files = [f for f in os.listdir(self.log_dir) if f.endswith(app_settings.LOG_TEMP_EXT)]

        if not log_files:
            self.logger.debug("No log files found in the directory.")
            return

        merged_content = self._merge_log_files(log_files)
        with open(output_file, "w", encoding="utf-8") as output:
            output.write(merged_content)
        self.logger.debug(f"All logs have been merged into '{output_file}'")

    def _merge_log_files(self, log_files: list) -> str:
        merged_content = ""
        for log_file in log_files:
            file_path = os.path.join(self.log_dir, log_file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                merged_content += (
                    f"\n\n====================[{log_file}]====================\n\n{content}"
                )
            os.remove(file_path)
        return merged_content


if __name__ == "__main__":
    custom_logger.setup_logging(logging.DEBUG)
    logger = logging.getLogger(__name__)

    config_loader = ConfigLoader(logger)
    config_loader.load_config()
    combined_paths = config_loader.get_combined_paths()

    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    log_dir = script_dir.parent / Path(app_settings.OUTPUT_DIR)
    file_syncer = FileSyncer(config_loader, logger)

    for key in combined_paths:
        file_syncer.sync_folders(
            combined_paths[key]["local_path"], combined_paths[key]["remote_path"]
        )
