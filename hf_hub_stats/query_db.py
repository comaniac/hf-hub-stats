"""Query database for useful insights."""
from .download_db import DownloadTrendDB
from .size_db import SizeDB, get_model_size_in_b_with_empty_weights
from .utils import draw_slope_chart, print_model_in_md


def query_top_models(args, print_markdown=False):
    # Load database.
    size_db = SizeDB(args.size_db)
    download_db = DownloadTrendDB(args.download_db)

    # Take the latest download counts and sort.
    all_models = sorted(
        download_db.latest() if args.date is None else download_db[args.date],
        key=lambda x: x.download,
        reverse=True,
    )

    # Whether to skip size checking.
    skip_size = args.min_size == 0 and args.max_size == float("inf")

    # Take top models in the given size range.
    models = []
    list_extra = 0
    start, end = args.start, min(args.end, len(all_models))
    for model in all_models[start:end]:
        model_id = model.model_id
        if skip_size:
            model.size = 0
        else:
            if model_id in size_db:
                result = size_db[model_id]
            else:
                result = get_model_size_in_b_with_empty_weights(model_id, fallback=True)

            if result.code != 0:
                if args.include_unsupported:
                    # Still include unsupported models.
                    list_extra += 1
                else:
                    continue
            elif result.size < args.min_size:
                # Ignore small models.
                continue
            elif result.size > args.max_size:
                # Ignore large models.
                continue

            model.size = result.size
        models.append(model)
        print(
            f"Appended {model_id}: {model.size}B params, now {len(models)} models,",
            f"target {args.limit + list_extra} models",
            flush=True,
        )

        # Stop when we have collected the target number of top models.
        if len(models) == args.limit + list_extra:
            break

    if print_markdown:
        print_model_in_md(models)
    return models


def query_model_size(model_ids, size_db, print_result=False):
    results = []
    for model_id in model_ids:
        if model_id in size_db:
            results.append(size_db[model_id])
        else:
            results.append(get_model_size_in_b_with_empty_weights(model_id, fallback=True))

        if print_result:
            print(results[-1])
    return results


def query_model_download(model_ids, date, download_db, print_result=False):
    model_id_set = set(model_ids)
    data = download_db.latest() if date is None else download_db[date]

    results = []
    for model_n_download in data:
        model_id = model_n_download.model_id
        if model_id in model_id_set:
            results.append(model_n_download)
            if print_result:
                print(model_n_download)
    return results


def draw_download_trend(args):
    import pandas as pd

    def size_in_range(size_db, model_id, min_size, max_size):
        result = query_model_size([model_id], size_db)[0]
        return result.code == 0 and result.size >= min_size and result.size <= max_size

    # Load database.
    size_db = SizeDB(args.size_db)
    download_db = DownloadTrendDB(args.download_db)

    # Whether to skip size checking.
    skip_size = args.min_size == 0 and args.max_size == float("inf")

    dates = download_db.dates(sort=True)

    # Get top models in the latest download counts.
    all_models = sorted(download_db[dates[-1]], key=lambda x: x.download, reverse=True)
    if skip_size:
        target_models = all_models[: args.limit]
    else:
        target_models = []
        for model in all_models:
            if not size_in_range(size_db, model.model_id, args.min_size, args.max_size):
                continue

            target_models.append(model)
            if len(target_models) == args.limit:
                break
    target_models = [m.model_id for m in target_models]

    # Take top models in the given size range.
    data = {}
    start_date = 0
    if args.max_history > 0 and args.max_history < len(dates):
        start_date = len(dates) - args.max_history
    for date in dates[start_date:]:
        data[date] = []

        # Find the rank of the target models.
        model_to_rank = {}
        sorted_model_n_download = sorted(download_db[date], key=lambda x: x.download, reverse=True)

        rank = 1
        for model_n_download in sorted_model_n_download:
            model_id = model_n_download.model_id
            if not (skip_size or size_in_range(size_db, model_id, args.min_size, args.max_size)):
                continue
            model_to_rank[model_id] = rank
            rank += 1

        for model in target_models:
            if model in model_to_rank:
                data[date].append(model_to_rank[model])
            else:
                data[date].append(float("inf"))

    draw_slope_chart(
        pd.DataFrame.from_dict(data, orient="index", columns=target_models),
        file_name=args.output,
        ylim=args.limit,
        line_args={"linewidth": 2, "alpha": 0.5},
        scatter_args={"s": 70, "alpha": 0.8},
    )
