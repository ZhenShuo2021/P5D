
# Todo: Logging if remote path exists.
import os
import re
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from src import config, custom_logger
from src.utils.file_utils import ConfigLoader



class FileSyncer:
    def __init__(self, config_loader: ConfigLoader, rsync_param: dict={}):
        self.logger = config_loader.logger
        self.log_dir = config_loader.log_dir
        self.config_loader = config_loader
        self.rsync_param = rsync_param.get("rsync", {})

    def sync_folders(self, src: str="", dst: str="") -> None:
        if not src:
            self.sync_folders_all()
        else:
            src, dst = Path(src), Path(dst)
            if not src.is_dir():
                self.logger.error(f"Local folder '{src}' not exist, terminate")
                raise FileNotFoundError
            if not dst.is_dir():
                self.logger.debug(f"Create nonexisting target folder '{str(self.log_dir)}'.")
                dst.mkdir(parents=True, exist_ok=True)

            log_path = self._log_name(self.log_dir, src)
            self._run_rsync(src, dst, log_path)

    def sync_folders_all(self) -> None:
        combined_paths = self.config_loader.get_combined_paths()
        for key in combined_paths:
            # Not using get method to prevent infinite loop
            if not combined_paths[key]["local_path"]:
                self.logger.error(
                    f"Local path of '{combined_paths[key]}' not found, continue to prevent infinite loop.")
                continue
            self.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])
        log_merger = LogMerger(self.config_loader)
        log_merger.merge_logs()

    def _log_name(self, log_dir: Path, src: Path) -> str:
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Creates folder '{log_dir}'")
        return os.path.join(str(log_dir), f'{os.path.basename(src)}{config.LOG_TEMP_EXT}')

    def _run_rsync(self, src: str, dst: str, log_path: str) -> None:
        if isinstance(self.rsync_param, str):
            rsync_options = self.rsync_param.split()
            
        if not self.rsync_param:
            command = [
                'rsync', '-aq', '--ignore-existing', '--progress',
                f'--log-file={log_path}', f'{src}/', f'{dst}/'
            ]
        else:
            command = [
            'rsync', *rsync_options, f'{src}/', f'{dst}/'
            ]
        self.logger.debug(f"Start Syncing '{src}' to '{dst}'.")
        subprocess.run(command, check=True)

class LogMerger:
    def __init__(self, config_loader: ConfigLoader):
        self.log_dir = config_loader.log_dir
        self.logger = config_loader.logger

    def merge_logs(self) -> None:
        output_file = f"{self.log_dir}/rsync_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        log_files = [f for f in os.listdir(self.log_dir) if f.endswith(config.LOG_TEMP_EXT)]

        if not log_files:
            self.logger.debug("No log files found in the directory.")
            return

        merged_content = self._merge_log_files(log_files)
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write(merged_content)
        self.logger.debug(f"All logs have been merged into '{output_file}'")

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
    custom_logger.setup_logging(logging.DEBUG)

    config_loader = ConfigLoader()
    config_loader.load_config()
    combined_paths = config_loader.get_combined_paths()
    
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    log_dir = script_dir.parent / Path(config.OUTPUT_DIR)
    file_syncer = FileSyncer(config_loader, log_dir)

    for key in combined_paths:
        file_syncer.sync_folders(combined_paths[key]["local_path"], combined_paths[key]["remote_path"])

    log_merger = LogMerger(config_loader)
    log_merger.merge_logs()
