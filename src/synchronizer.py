
# Todo: Logging if remote path exists.
import os
import subprocess
from datetime import datetime
from pathlib import Path

from utils.file_utils import ConfigLoader
from src.logger import LogLevel, LogManager, logger

TEMP_NAME = ".logfile"


class FileSyncer:
    def __init__(self, config_loader: ConfigLoader, log_dir: Path, logger: LogManager):
        self.logger = logger
        self.log_dir = log_dir
        self.config_loader = config_loader

    def sync_folders(self, src: str="", dst: str="") -> None:
        if not src:
            self.sync_folders_all()
        else:
            src, dst = Path(src), Path(dst)
            if not src.is_dir():
                self.logger.critical(f"Local folder '{src}' not exist, terminate")
                raise FileNotFoundError
            if not dst.is_dir():
                self.logger.debug(f"Create nonexisting target folder '{str(self.log_dir)}'.")
                dst.mkdir(parents=True, exist_ok=True)

            log_path = self._log_name(self.log_dir, src)
            self._run_rsync(src, dst, log_path)

    def sync_folders_all(self):
        combined_paths = self.config_loader.get_combined_paths()
        for key in combined_paths:
            if not combined_paths[key]["local_path"]:
                self.logger.critical(
                    f"Local path of '{combined_paths[key]}' not found, continue to prevent infinite loop.")
                continue
            self.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])
        log_merger = LogMerger(self.log_dir)
        log_merger.merge_logs()

    def _log_name(self, log_dir: Path, src: Path) -> str:
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Creates folder '{log_dir}'")
        return os.path.join(str(log_dir), f'{os.path.basename(src)}{TEMP_NAME}')

    def _run_rsync(self, src: str, dst: str, log_path: str) -> None:
        command = [
            'rsync', '-aq', '--ignore-existing', '--progress',
            f'--log-file={log_path}', f'{src}/', f'{dst}/'
        ]
        print(command)
        self.logger.debug(f"Start Syncing '{src}' to '{dst}'.")
        subprocess.run(command, check=True)

class LogMerger:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir

    def merge_logs(self):
        output_file = f"{self.log_dir}/rsync_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        log_files = [f for f in os.listdir(self.log_dir) if f.endswith(TEMP_NAME)]

        if not log_files:
            print("No log files found in the directory.")
            return

        merged_content = self._merge_log_files(log_files)
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(merged_content)
        print(f"All logs have been merged into {output_file}")

    def _merge_log_files(self, log_files: list) -> str:
        merged_content = ""
        for log_file in log_files:
            file_path = os.path.join(self.log_dir, log_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                merged_content += f"\n\n====================[{log_file}]====================\n\n{content}"
            os.remove(file_path)
        return merged_content

if __name__ == "__main__":
    log_manager = LogManager(level=LogLevel.DEBUG, status="synchronizer.py")
    logger = log_manager.get_logger()

    config_loader = ConfigLoader('config/config.toml')
    combined_paths = config_loader.get_combined_paths()
    
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    log_dir = script_dir.parent / Path("data")
    file_syncer = FileSyncer(config_loader, log_dir, logger)

    for key in combined_paths:
        file_syncer.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])

    log_merger = LogMerger(log_dir)
    log_merger.merge_logs()
