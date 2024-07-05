from pathlib import Path

VALID_IMAGE_EXTENSIONS = {'.jpg', '.png', '.jpeg', '.jfif', '.webp', '.gif'}


def glob_local_files(path: Path, pattern: str = "*", valid_extensions: set[str] = None):
    if valid_extensions is None:
        valid_extensions = VALID_IMAGE_EXTENSIONS

    for file in path.glob(pattern):
        if file.suffix.lower() in valid_extensions:
            yield file
