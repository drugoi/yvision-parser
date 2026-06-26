import argparse
from pathlib import Path

from exporter import export_account


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yvision-parser",
        description="Export a yvision.kz blog account's posts to Markdown.",
    )
    parser.add_argument(
        "account",
        help="yvision username, profile URL (https://<name>.yvision.kz), or numeric user id",
    )
    parser.add_argument(
        "--output",
        default="posts",
        help="base output directory (posts are written under <output>/<username>/). Default: posts",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="do not download images; keep external image URLs in the Markdown",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    def on_progress(done: int, total: int, phase: str) -> None:
        print(f"  [{done}/{total}] saved")

    result = export_account(
        args.account,
        Path(args.output),
        include_images=not args.no_images,
        on_progress=on_progress,
    )

    print(f"\nDone! {result.saved} posts saved for {result.username}.")


if __name__ == "__main__":
    main()
