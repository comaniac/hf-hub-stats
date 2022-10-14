"""CLI Entry point."""
import argparse

from .query_hub import query_hf_hub
from .query_db import query_top_models, query_model_size, draw_download_trend, query_model_download
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

    # CLI for querying top downloaded models.
    query_top_parser = subprasers.add_parser(
        "query_top", parents=[common_parser], help="Query top download models from download DB"
    )
    query_top_parser.add_argument(
        "--download-db", type=str, required=True, help="The path to download trend database in JSON"
    )
    query_top_parser.add_argument(
        "--size-db", type=str, help="The path to model size database in JSON"
    )
    query_top_parser.add_argument(
        "--date",
        type=str,
        help="The date in %m-%d-%y format to query the top models."
        "The latest date in the download DB will be used if unspecified.",
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
    query_top_parser.add_argument(
        "--include-unsupported", action="store_true", help="Include unsupported models"
    )

    # CLI for updating the size database.
    size_db_parser = subprasers.add_parser(
        "update_size_db", parents=[common_parser], help="Update size database"
    )
    size_db_parser.add_argument(
        "--size-db", type=str, required=True, help="The path to model size database in JSON"
    )

    # CLI for querying the model size.
    query_size_parser = subprasers.add_parser(
        "query_size", parents=[common_parser], help="Query model size"
    )
    query_size_parser.add_argument(
        "--size-db", type=str, required=True, help="The path to model size database in JSON"
    )
    query_size_parser.add_argument(
        "--model-ids", nargs="+", required=True, help="The model ID to query"
    )

    # CLI for updating the download trend database.
    download_db_parser = subprasers.add_parser(
        "update_download_trend_db", parents=[common_parser], help="Update download trend database"
    )
    download_db_parser.add_argument(
        "--download-db", type=str, required=True, help="The path to database in JSON"
    )

    # CLI for querying the model download.
    query_download_parser = subprasers.add_parser(
        "query_download", parents=[common_parser], help="Query model download times"
    )
    query_download_parser.add_argument(
        "--download-db", type=str, required=True, help="The path to download time database in JSON"
    )
    query_download_parser.add_argument(
        "--model-ids", nargs="+", required=True, help="The model ID to query"
    )
    query_download_parser.add_argument(
        "--date",
        type=str,
        help="The date in %m-%d-%y format to query."
        "The latest date in the download DB will be used if unspecified.",
    )

    # CLI for drawing download trend.
    draw_download_trend_parser = subprasers.add_parser(
        "draw_download_trend", parents=[common_parser], help="Draw download trends"
    )
    draw_download_trend_parser.add_argument(
        "--limit", type=int, default=20, help="The maximum number of returned models"
    )
    draw_download_trend_parser.add_argument(
        "--size-db", type=str, help="The path to model size database in JSON"
    )
    draw_download_trend_parser.add_argument(
        "--download-db", type=str, required=True, help="The path to download time database in JSON"
    )
    draw_download_trend_parser.add_argument(
        "--min-size", type=float, default=0, help="The minimum model size in billions"
    )
    draw_download_trend_parser.add_argument(
        "--max-size", type=float, default=float("inf"), help="The maximum model size in billions"
    )
    draw_download_trend_parser.add_argument(
        "--max-history",
        type=int,
        default=0,
        help="The maximum number of records to draw." "Default 0 draws all records.",
    )
    draw_download_trend_parser.add_argument("-o", "--output", type=str, help="The output file name")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.mode == "update_size_db":
        SizeDB(args.size_db).update(query_hf_hub(), args)
    elif args.mode == "update_download_trend_db":
        DownloadTrendDB(args.download_db).update(query_hf_hub(), args)
    elif args.mode == "draw_download_trend":
        draw_download_trend(args)
    elif args.mode == "query_top":
        query_top_models(args, print_markdown=True)
    elif args.mode == "query_download":
        query_model_download(
            args.model_ids, args.date, DownloadTrendDB(args.download_db), print_result=True
        )
    elif args.mode == "query_size":
        query_model_size(args.model_ids, SizeDB(args.size_db), print_result=True)


if __name__ == "__main__":
    main()
