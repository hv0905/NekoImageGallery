import itertools
from pathlib import Path

from loguru import logger

from app.util import generate_uuid


def gather_valid_files(root: Path, pattern: str = '**/*.*', max_files=None):
    valid_extensions = {'.jpg', '.png', '.jpeg', '.jfif', '.webp', '.gif'}

    def file_generator():
        for file in root.glob(pattern):
            if file.suffix.lower() in valid_extensions:
                yield file
            else:
                logger.warning(f"Unsupported file type: {file.suffix}. Skipping file: {file}")

    def generator():
        gen = file_generator()
        if max_files is None:
            yield from gen
        else:
            while True:
                batch = list(itertools.islice(gen, max_files))
                if not batch:
                    break
                yield batch

    return generator()


def calculate_uuid(file_path: Path) -> str:
    return str(generate_uuid.generate(file_path))


def fetch_path_uuid_list(file_path: Path | list[Path]) -> list[tuple[Path, str]]:
    file_path = [file_path] if isinstance(file_path, Path) else file_path
    return [(itm, calculate_uuid(itm)) for itm in file_path]
