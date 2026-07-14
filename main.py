import argparse
import sys

from app.clients.database_client import upgrade_database
from app.configs.run_logging import setup_logging
from app.configs.settings import get_settings
from app.controllers.invitation_controllers import InvitationExtractionError, extract_invitations
from app.controllers.invitation_controllers.sap_invitation_extractor import SapInvitationExtractor
from app.controllers.selenuim_client import SapClient, SapClientError


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
        help="Extract Sales Enquiry invitations (--mode today|yesterday|all)",
    )
    invitations_parser.add_argument(
        "--mode",
        choices=["today", "yesterday", "all"],
        default="today",
        help="today: Document Date=Today; yesterday: Document Date=Yesterday; all: Go only (no date filter)",
    )
    invitations_parser.add_argument(
        "--visible",
        action="store_true",
        help="Show the browser window during extraction",
    )

    extract_subparsers.add_parser(
        "cases",
        help="Extract Case Registration records and RFQ items",
    )

    db_parser = subparsers.add_parser("db", help="Database management")
    db_subparsers = db_parser.add_subparsers(dest="db_action", required=True)
    db_subparsers.add_parser("upgrade", help="Apply Alembic migrations to head")

    sap_parser = subparsers.add_parser("sap", help="SAP Fiori browser automation")
    sap_subparsers = sap_parser.add_subparsers(dest="sap_action", required=True)
    sap_test_parser = sap_subparsers.add_parser(
        "test",
        help="Login to SAP and open Manage Sales Enquiries",
    )
    sap_test_parser.add_argument(
        "--visible",
        action="store_true",
        help="Show the browser window (overrides HEADLESS=true behavior)",
    )
    sap_test_parser.add_argument(
        "--keep-open",
        type=int,
        default=0,
        help="Keep browser open for N seconds before closing",
    )

    api_parser = subparsers.add_parser("api", help="Run the HTTP API server")
    api_subparsers = api_parser.add_subparsers(dest="api_action", required=True)
    api_serve_parser = api_subparsers.add_parser("serve", help="Start the API server")
    api_serve_parser.add_argument("--host", default=None, help="Override API_HOST")
    api_serve_parser.add_argument("--port", type=int, default=None, help="Override API_PORT")
    api_serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    return parser


def run_extract_invitations(args: argparse.Namespace) -> int:
    logger = setup_logging(run_name="invitations")
    settings = get_settings()
    headless = False if args.visible else settings.headless
    mode = args.mode

    try:
        logger.info(
            "Fetching invitations mode=%s (limit=%s)",
            mode,
            settings.sap_max_invitations if settings.sap_max_invitations > 0 else "unlimited",
        )
        saved = extract_invitations(
            mode=mode,
            headless=headless,
            settings=settings,
        )
    except InvitationExtractionError:
        logger.exception("Invitation extraction failed")
        return 1

    logger.info("Done. %s invitation(s) saved to database.", saved)
    return 0


def run_extract_cases() -> int:
    logger = setup_logging(run_name="cases")
    logger.info("Case extraction is not implemented yet (Step 5).")
    return 0


def run_sap_test(args: argparse.Namespace) -> int:
    logger = setup_logging(run_name="sap_test")
    settings = get_settings()
    headless = False if args.visible else settings.headless

    try:
        with SapClient(headless=headless) as client:
            client.login()
            logger.info("Login OK — title: %s", client.page_title)
            extractor = SapInvitationExtractor(client)
            extractor.prepare_search(mode="today")
            logger.info("Navigation OK — URL: %s", client.current_url)

            client.keep_open(args.keep_open)
    except SapClientError:
        logger.exception("SAP test failed")
        return 1

    logger.info("SAP test completed successfully")
    return 0


def run_db_upgrade() -> int:
    logger = setup_logging(run_name="db_upgrade")
    logger.info("Applying database migrations...")
    upgrade_database()
    logger.info("Database migrations applied successfully.")
    return 0


def run_api_serve(args: argparse.Namespace) -> int:
    import uvicorn

    settings = get_settings()
    host = args.host or settings.api_host
    port = args.port or settings.api_port
    logger = setup_logging(run_name="api")
    logger.info("Starting API server at http://%s:%s", host, port)
    uvicorn.run("app.main:app", host=host, port=port, reload=args.reload)
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
    if args.command == "sap" and args.sap_action == "test":
        return run_sap_test(args)
    if args.command == "api" and args.api_action == "serve":
        return run_api_serve(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
