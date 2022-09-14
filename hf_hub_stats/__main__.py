"""CLI Entry point."""
import argparse

from .query_hub import query_hf_hub
from .query_top_models import get_top_models
from .size_db import SizeDB
from .download_db import DownloadTrendDB


def parse_args():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--start", type=int, default=0, help="Start with top-n th model")
    common_parser.add_argument(
        "--end", type=int, default=float("inf"), help="Stop at top-n th model"
    )
    parser = argparse.ArgumentParser()
    subprasers = parser.add_subparsers(dest="mode", help="Execution modes")

    query_top_parser = subprasers.add_parser(
        "query_top", parents=[common_parser], help="Query top download models"
    )
    query_top_parser.add_argument(
        "--db", type=str, help="The path to model size database in JSON"
    )
    query_top_parser.add_argument(
        "--limit", type=int, default=20, help="The maximum number of returned models"
    )
    query_top_parser.add_argument(
        "--min-size", type=float, default=0, help="The minimum model size in billions"
    )
    query_top_parser.add_argument(
        "--max-size", type=float, default=float("inf"), help="The maximum model size in billions"
    )

    size_db_parser = subprasers.add_parser(
        "update_size_db", parents=[common_parser], help="Update size database"
    )
    size_db_parser.add_argument(
        "--db", type=str, required=True, help="The path to model size database in JSON"
    )

    download_db_parser = subprasers.add_parser(
        "update_download_trend_db", parents=[common_parser], help="Update download trend database"
    )
    download_db_parser.add_argument(
        "--db", type=str, required=True, help="The path to database in JSON"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    all_models = query_hf_hub()

    if args.mode == "update_size_db":
        SizeDB(args.db).update(all_models, args)
    elif args.mode == "update_download_trend_db":
        DownloadTrendDB(args.db).update(all_models, args)
    elif args.mode == "query_top":
        get_top_models(all_models, args, print_markdown=True)


if __name__ == "__main__":
    main()
