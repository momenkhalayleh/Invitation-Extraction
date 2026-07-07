import argparse
import sys

from alembic import command
from alembic.config import Config

from app.configs.run_logging import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Al Ghanem SAP data extraction CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser(
        "extract",
        help="Run an extraction job against SAP",
    )
    extract_subparsers = extract_parser.add_subparsers(dest="domain", required=True)

    invitations_parser = extract_subparsers.add_parser(
        "invitations",
        help="Extract Sales Enquiry (invitation) records",
    )
    invitations_parser.add_argument(
        "--from-date",
        dest="date_from",
        help="Override SCRAPE_DATE_FROM (YYYY-MM-DD)",
    )
    invitations_parser.add_argument(
        "--to-date",
        dest="date_to",
        help="Override SCRAPE_DATE_TO (YYYY-MM-DD)",
    )

    extract_subparsers.add_parser(
        "cases",
        help="Extract Case Registration records and RFQ items",
    )

    db_parser = subparsers.add_parser("db", help="Database management")
    db_subparsers = db_parser.add_subparsers(dest="db_action", required=True)
    db_subparsers.add_parser("upgrade", help="Apply Alembic migrations to head")

    return parser


def run_extract_invitations(args: argparse.Namespace) -> int:
    logger = setup_logging(run_name="invitations")
    logger.info("Invitation extraction is not implemented yet (Step 4).")
    if args.date_from or args.date_to:
        logger.info("Date override: from=%s to=%s", args.date_from, args.date_to)
    return 0


def run_extract_cases() -> int:
    logger = setup_logging(run_name="cases")
    logger.info("Case extraction is not implemented yet (Step 5).")
    return 0


def run_db_upgrade() -> int:
    logger = setup_logging(run_name="db_upgrade")
    logger.info("Applying database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract" and args.domain == "invitations":
        return run_extract_invitations(args)
    if args.command == "extract" and args.domain == "cases":
        return run_extract_cases()
    if args.command == "db" and args.db_action == "upgrade":
        return run_db_upgrade()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
