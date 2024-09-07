# Todo: Logging if remote path exists.
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from p5d import custom_logger
from p5d.app_settings import LOG_TEMP_EXT, USER_OS, TEMP_DIR
from p5d.utils import ConfigLoader, normalize_path


class FileSyncer:
    def __init__(
        self,
        config_loader: ConfigLoader,
        logger: logging.Logger,
        rsync_param: dict = {},
        direct_sync: bool = False,
    ):
        self.logger = logger
        self.output_dir = config_loader.get_output_dir()
        self.config_loader = config_loader
        self.rsync_param = self.update_param(config_loader.get_custom(), rsync_param)
        self.direct_sync = direct_sync

    def sync_folders(self, src: Any, dst: Any) -> None:
        """Sync folder with rsync."""
        if not src:
            self.sync_folders_all()
        else:
            src, dst = Path(src), Path(dst)
            if not self.direct_sync:
                if not src.is_dir():
                    self.logger.error(f"Syncing file error: local folder '{src}' not exist.")
                if not dst.is_dir():
                    self.logger.debug(f"Create nonexisting target folder '{str(self.output_dir)}'.")
                    dst.mkdir(parents=True, exist_ok=True)

            log_path = self._log_name(self.output_dir, src)
            self._run_rsync(src, dst, log_path)

    def sync_folders_all(self) -> None:
        combined_paths = self.config_loader.get_combined_paths()
        for key in combined_paths:
            if not combined_paths.get(key, {}).get("local_path", {}):
                self.logger.error(
                    f"Local path of '{combined_paths[key]}' not found, continue to prevent infinite loop."
                )
                continue
            self.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])
        log_merger = LogMerger(self.output_dir, self.logger)
        log_merger.merge_logs()

    def _log_name(self, output_dir: Path, src: Path) -> str:
        if not output_dir.is_dir():
            output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Creates folder '{output_dir}'")
        return os.path.join(str(output_dir), f"{os.path.basename(src)}{LOG_TEMP_EXT}")

    def _run_rsync(self, src: str | Path, dst: str | Path, log_path: str | Path) -> None:
        command = ["rsync", "-aq", "--ignore-existing", "--progress"]
        if self.direct_sync:
            while True:
                dst = self._process_mapping_file()  # type: ignore
                if dst is None:
                    break
                Path(dst).mkdir(parents=True, exist_ok=True)
                dst = normalize_path(self.add_slash(dst))
                mapping_file = os.path.join(TEMP_DIR, "files.txt")

                if not os.path.getsize(os.path.join(TEMP_DIR, "files.txt")):
                    self.logger.debug("Mapping file is empty or only contains blank lines.")
                    break

                command += ["--no-relative", f"--files-from={mapping_file}", "/", dst]
                if self.rsync_param:
                    rsync_options = self.rsync_param.split()
                    command = [
                        "rsync",
                        *rsync_options,
                        "--no-relative",
                        f"--files-from={mapping_file}",
                        "/",
                        dst,
                    ]

                self.logger.debug(f"Start Syncing with command: {' '.join(command)}")
                try:
                    subprocess.run(
                        command, check=True, capture_output=True, text=True, encoding="utf-8"
                    )
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Synchronization failed: {e}")
        else:
            src = normalize_path(self.add_slash(src))
            dst = normalize_path(self.add_slash(dst))
            command += [f"--log-file={log_path}", src, dst]
            if self.rsync_param:
                rsync_options = self.rsync_param.split()
                command = ["rsync", *rsync_options, f"{src}", f"{dst}"]

            self.logger.debug(f"Start Syncing '{src}' to '{dst}'.")
            try:
                subprocess.run(
                    command, check=True, capture_output=True, text=True, encoding="utf-8"
                )
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Synchronization failed: {e}")

    def _process_mapping_file(self) -> Optional[str]:
        filename = os.path.join(TEMP_DIR, "mapping.txt")
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()

        key = None
        values = []

        for line in lines:
            line = line.strip()
            if line.startswith("[key]"):
                if key is not None:
                    break
                key = line[5:]
            elif line.startswith("[value]"):
                values.append(line[7:])

        with open(os.path.join(TEMP_DIR, "files.txt"), "w", encoding="utf-8") as temp_file:
            for value in values:
                temp_file.write(value + "\n")

        remaining_lines = lines[len(values) + 1 :]

        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(remaining_lines)
        return key

    def update_param(self, file_input: dict[str, str], cmd_input: dict[str, str]) -> str:
        """Overwrite rsync parameter"""
        return cmd_input.get("rsync", "") or file_input.get("rsync", "") or ""

    def add_slash(self, path: str | Path) -> str:
        return rf"{str(path)}\\" if USER_OS == "Windows" else f"{str(path)}/"


class LogMerger:
    def __init__(self, output_dir: Path, logger: logging.Logger):
        self.output_dir = output_dir
        self.logger = logger

    def merge_logs(self) -> None:
        output_file = self.output_dir / Path("rsync.log")
        log_files = [f for f in os.listdir(self.output_dir) if f.endswith(LOG_TEMP_EXT)]

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
            file_path = os.path.join(self.output_dir, log_file)
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
    output_dir = config_loader.get_output_dir()
    file_syncer = FileSyncer(config_loader, logger)

    for key in combined_paths:
        file_syncer.sync_folders(
            combined_paths[key]["local_path"], combined_paths[key]["remote_path"]
        )
