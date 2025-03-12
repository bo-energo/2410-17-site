from pathlib import Path


def get_path_log_dir(base_dir: Path, log_dir: str):
    """Возвращает путь до директории логов"""
    path_logs_dir = base_dir.resolve().parents[0].joinpath(log_dir)
    if not path_logs_dir.exists():
        path_logs_dir.mkdir()
    return path_logs_dir
