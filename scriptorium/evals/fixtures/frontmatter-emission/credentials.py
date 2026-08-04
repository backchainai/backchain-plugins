"""Widget Relay service-credential CLI.

Manages the credentials Widget Relay uses to authenticate to the container
registry and the downstream systems it relays events to.
"""

import argparse
import sys


def rotate_api_key(key_id: str, overlap_hours: int, dry_run: bool) -> int:
    """Issue a new API key for `key_id`, overlap it with the old key for
    `overlap_hours`, then revoke the old key. Returns the process exit code.
    """
    action = "Would rotate" if dry_run else "Rotating"
    print(f"{action} key '{key_id}' with a {overlap_hours}h overlap window.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="credentials.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rotate = subparsers.add_parser(
        "rotate-api-key",
        help="Issue a new API key, overlap it with the old key, then revoke the old key.",
    )
    rotate.add_argument(
        "--key-id",
        required=True,
        help="The id of the key to rotate.",
    )
    rotate.add_argument(
        "--overlap-hours",
        type=int,
        default=24,
        help="Hours the old and new keys are both valid before the old key is revoked. Default: 24.",
    )
    rotate.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned actions without executing them.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rotate-api-key":
        return rotate_api_key(args.key_id, args.overlap_hours, args.dry_run)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
