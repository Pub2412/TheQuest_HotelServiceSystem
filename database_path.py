import os
import sys
from pathlib import Path


DATABASE_FILENAME = "hotel_service.db"
DATABASE_ENVIRONMENT_VARIABLE = "QUEST_HOTEL_DATABASE"


def get_database_path() -> Path:
    """Return the shared writable database path, with a source-tree fallback."""
    configured_path = os.environ.get(DATABASE_ENVIRONMENT_VARIABLE)
    if configured_path:
        return Path(configured_path)

    program_data = os.environ.get("PROGRAMDATA")
    if program_data:
        installed_path = (
            Path(program_data)
            / "The Quest Hotel"
            / "database"
            / DATABASE_FILENAME
        )
        if installed_path.exists():
            return installed_path

    executable_dir = Path(sys.executable).resolve().parent
    packaged_path = executable_dir / "database" / DATABASE_FILENAME
    if packaged_path.exists():
        return packaged_path

    return Path(__file__).resolve().parent / "database" / DATABASE_FILENAME
