# Todo: Logging if remote path exists.
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from p5d import custom_logger
from p5d.app_settings import RSYNC_TEMP_EXT, USER_OS, TEMP_DIR
from p5d.utils import ConfigLoader, normalize_path, extract_opt


class SyncStrategy(ABC):
    def __init__(self) -> None:
        self.cmd_base = ["rsync", "-aq", "--ignore-existing", "--progress"]

    @abstractmethod
    def sync(self, src: Path, dst: Path, log_path: Path) -> None:
        pass


class RsyncStrategy(SyncStrategy):
    def __init__(self, rsync_param: list[str]) -> None:
        super().__init__()
        self.rsync_param = rsync_param

    def sync(self, src: Path, dst: Path, log_path: Path) -> None:
        cmd = self.cmd_base + [f"--log-file={log_path}", str(_add_slash(src)), str(dst)]
        if self.rsync_param:
            cmd = ["rsync"] + self.rsync_param + [str(src), str(dst)]

        try:
            subprocess.run(cmd, check=True, text=True, encoding="utf-8")
        except subprocess.CalledProcessError as e:
            raise SyncError(f"Synchronization failed: {e}")


class DirectSyncStrategy(SyncStrategy):
    def __init__(self, rsync_param: list[str], config_loader: ConfigLoader):
        super().__init__()
        self.rsync_param = rsync_param
        self.config_loader = config_loader

    def sync(self, src: str | Path, dst: str | Path, log_path: Path) -> None:
        while True:
            dst = self._process_mapping_file()  # type: ignore
            if dst is None:
                break

            Path(dst).mkdir(parents=True, exist_ok=True)
            dst = normalize_path(_add_slash(dst))
            mapping_file = normalize_path(
                os.path.join(self.config_loader.base_dir, TEMP_DIR, "files.txt")
            ).rstrip("/")

            if not os.path.getsize(os.path.join(TEMP_DIR, "files.txt")):
                break

            cmd = self.cmd_base + ["--no-relative", f"--files-from={mapping_file}", "/", dst]
            if self.rsync_param:
                cmd = (
                    ["rsync"]
                    + self.rsync_param
                    + ["--no-relative", f"--files-from={mapping_file}", "/", dst]
                )

            try:
                subprocess.run(cmd, check=True, text=True, encoding="utf-8")
            except subprocess.CalledProcessError as e:
                raise SyncError(f"Synchronization failed: {e}")

    def _process_mapping_file(self) -> str | None:
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


class FileSyncer:
    def __init__(
        self,
        config_loader: ConfigLoader,
        logger: logging.Logger,
        direct_sync: bool = False,
        args: dict[str, Any] = {},
    ):
        self.logger = logger
        self.config_loader = config_loader
        rsync_param = self._update_param(config_loader.get_custom(), args)
        rsync_param = extract_opt(rsync_param)

        if direct_sync:
            self.sync_strategy = DirectSyncStrategy(rsync_param, config_loader)
        else:
            self.sync_strategy = RsyncStrategy(rsync_param)

    def sync_folders(self, src: Any, dst: Any) -> None:
        if not src:
            self.sync_folders_all()
        else:
            src, dst = Path(src), Path(dst)
            if not isinstance(self.sync_strategy, DirectSyncStrategy):
                if not src.is_dir():
                    raise SyncError(f"Syncing file error: local folder '{src}' does not exist.")
                if not dst.is_dir():
                    self.logger.debug(f"Create nonexisting target folder '{str(dst)}'.")
                    dst.mkdir(parents=True, exist_ok=True)

            log_path = self._log_name(self.config_loader.base_dir / TEMP_DIR, src)
            try:
                self.sync_strategy.sync(src, dst, log_path)
            except SyncError as e:
                self.logger.error(str(e))

    def sync_folders_all(self) -> None:
        combined_paths = self.config_loader.get_combined_paths()
        for key, paths in combined_paths.items():
            if not paths.get("local_path"):
                self.logger.error(
                    f"Local path of '{paths}' not found, continue to prevent infinite loop."
                )
                continue
            self.sync_folders(paths["local_path"], paths["remote_path"])

    def _log_name(self, output_dir: Path, src: Path) -> Path:
        if not output_dir.is_dir():
            output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Creates folder '{output_dir}'")
        return output_dir / f"{src.name}{RSYNC_TEMP_EXT}"

    def _update_param(self, file_input: dict[str, str], cmd_input: dict[str, str]) -> str:
        return cmd_input.get("rsync", "") or file_input.get("rsync", "") or ""


def _add_slash(path: str | Path) -> str:
    return rf"{path}\\" if USER_OS == "Windows" else f"{path}/"


class SyncError(Exception):
    pass


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
