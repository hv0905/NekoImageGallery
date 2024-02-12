from pathlib import Path
from app.util import generate_uuid


def calculate_uuid(file_path: Path) -> str:
    return str(generate_uuid.generate(file_path))


def fetch_path_uuid_list(file_path: Path | list[Path]) -> list[tuple[Path, str]]:
    file_path = [file_path] if isinstance(file_path, Path) else file_path
    return [(itm, calculate_uuid(itm)) for itm in file_path]
