"""The database of model download trends."""
import datetime
import os

import json
from dataclasses import asdict, dataclass


@dataclass
class DateNDownload:
    """The dataclass of download count in the past 30 days since the date."""

    model_id: str
    date: str
    download: int


class DownloadTrendDB:
    def __init__(self, file_name):
        self.file_name = file_name
        self.db = {}
        if os.path.exists(file_name):
            with open(file_name, "r") as filep:
                for key, val in json.load(filep).items():
                    self.db[key] = [DateNDownload(**v) for v in val]
            print(f"{len(self.db)} record loaded from the download trend DB", flush=True)

    def __getitem__(self, key):
        return self.db[key]

    def __contains__(self, key):
        return key in self.db

    def __len__(self):
        return len(self.db)

    def __setitem__(self, key, date_n_download):
        model_id = date_n_download.model_id
        assert key == model_id

        if model_id not in self.db:
            self.db[model_id] = []
        self.db[model_id].append(date_n_download)

    def persist(self):
        print(f"Updating database with total {len(self.db)} records", flush=True)
        with open(self.file_name, "w") as filep:
            data = {k: [asdict(vv) for vv in v] for k, v in self.db.items()}
            json.dump(data, filep, indent=2)

    def update(self, all_models, args):
        today = str(datetime.datetime.today())
        for model in all_models[args.start: min(args.end, len(all_models))]:
            model_id = model.modelId
            if not hasattr(model, "downloads"):
                continue
            self[model_id] = DateNDownload(model_id, today, model.downloads)

        self.persist()
