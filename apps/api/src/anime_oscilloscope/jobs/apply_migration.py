import argparse
from pathlib import Path

from anime_oscilloscope.config import get_settings
from anime_oscilloscope.database import PostgresDatabase


def apply(path: Path) -> None:
    resolved = path.resolve()
    if resolved.suffix.lower() != ".sql" or "migrations" not in resolved.parts:
        raise ValueError("only SQL files inside a migrations directory may be applied")
    sql = resolved.read_text(encoding="utf-8")
    settings = get_settings()
    with PostgresDatabase(settings.database_url).connection() as connection:
        connection.execute(sql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply one idempotent database migration")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    apply(args.path)
    print(f"Applied migration: {args.path}")


if __name__ == "__main__":
    main()
