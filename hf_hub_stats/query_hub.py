"""Query Hugging Face hub."""
import datetime

import os
import pickle

from huggingface_hub import HfApi, ModelFilter


def query_hf_hub(cache_expire=7):
    """Query Huggingface Hub with filter."""
    cache_folder = os.path.join(os.path.expanduser("~"), ".cache/query_hf_hub/")
    cache_file = os.path.join(cache_folder, "all_models.pkl")

    # Directly use local cached model list if available and
    # not expired (7 days).
    if os.path.exists(cache_file):
        today = datetime.datetime.today()
        modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
        duration = today - modified_date
        if duration.days <= cache_expire:
            print(f"Using cached model list (queried in {duration.days} days)", flush=True)
            with open(cache_file, "rb") as filep:
                return pickle.load(filep)
        else:
            print(f"Updating cached model list (queried in {duration.days} days)", flush=True)
    else:
        print(f"Querying model list", flush=True)
        os.makedirs(cache_folder, exist_ok=True)

    api = HfApi()
    custom_filter = ModelFilter(library="pytorch")

    # sort="downloads" doesn't work so we sort by ourselves.
    all_models = api.list_models(filter=custom_filter)

    # Remove the models with downloads=0.
    all_models = [m for m in all_models if hasattr(m, "downloads")]

    # Sort models by downloads.
    all_models = sorted(all_models, key=lambda m: m.downloads, reverse=True)

    # Cache results.
    with open(cache_file, "wb") as filep:
        pickle.dump(all_models, filep)

    return all_models
