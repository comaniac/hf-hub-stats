from .size_db import SizeDB, get_model_size_in_b_with_empty_weights


def print_model_in_md(models):
    from tabulate import tabulate

    data = []
    for rank, model in enumerate(models):
        if model.size == 0:
            size = "N/A"
        elif model.size == -1:
            size = "Unsupported"
        elif model.size < 1:
            size = "{:.0f}M".format(model.size * 1e3)
        else:
            size = "{:.1f}B".format(model.size)
        data.append((rank + 1, model.modelId, model.downloads, size))

    print(tabulate(data, headers=["Rank", "Name", "Downloads", "Size"]))


def get_top_models(all_models, args, print_markdown=False):
    # Load model size database if available.
    size_db = SizeDB(args.db)

    # Whether to skip size checking.
    skip_size = args.min_size == 0 and args.max_size == float("inf")

    # Take top models in the given size range.
    models = []
    list_extra = 0
    start, end = args.start, min(args.end, len(all_models))
    for model in all_models[start : end]:
        model_id = model.modelId
        if skip_size:
            model.size = 0
        else:
            if model_id in size_db:
                result = size_db[model_id]
            else:
                result = get_model_size_in_b_with_empty_weights(model_id, fallback=True)

            if result.code != 0:
                # Still include unsupported models.
                list_extra += 1
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
