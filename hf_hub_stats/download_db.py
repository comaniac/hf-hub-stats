"""The database of model download trends."""
from typing import List
import datetime
import os

import json
from dataclasses import asdict, dataclass


@dataclass
class ModelNDownload:
    """The dataclass of download count in the past 30 days of a model."""

    model_id: str
    download: int


class DownloadTrendDB:
    def __init__(self, file_name):
        self.file_name = file_name
        self.db = {}
        if os.path.exists(file_name):
            with open(file_name, "r") as filep:
                for key, val in json.load(filep).items():
                    self.db[key] = [ModelNDownload(**v) for v in val]
            print(f"{len(self.db)} records loaded from the download trend DB", flush=True)

    def __getitem__(self, key):
        return self.db[key]

    def __contains__(self, key):
        return key in self.db

    def __len__(self):
        return len(self.db)

    def latest(self) -> str:
        dates = sorted([datetime.datetime.strptime(d, "%m-%d-%y") for d in self.db.keys()])
        return self.db[dates[-1].strftime("%m-%d-%y")]

    def dates(self, sort=False) -> List[str]:
        ret = [datetime.datetime.strptime(d, "%m-%d-%y") for d in self.db.keys()]
        ret = sorted(ret) if sort else ret
        return [r.strftime("%m-%d-%y") for r in ret]

    def persist(self):
        print(f"Updating database with total {len(self.db)} records", flush=True)
        with open(self.file_name, "w") as filep:
            data = {k: [asdict(vv) for vv in v] for k, v in self.db.items()}
            json.dump(data, filep, indent=2)

    def update(self, all_models, args):
        today = datetime.datetime.today().strftime("%m-%d-%y")
        if today not in self.db:
            self.db[today] = []
        for model in all_models[args.start : min(args.end, len(all_models))]:
            if not hasattr(model, "downloads"):
                continue
            self.db[today].append(ModelNDownload(model.modelId, model.downloads))

        self.persist()

    def prune(self, max_records=10):
        dates = sorted([datetime.datetime.strptime(d, "%m-%d-%y") for d in self.db.keys()])
        if max_records >= len(dates):
            print(f"Skip pruning because {max_records} >= {len(dates)}", flush=True)
            return
        tbd = len(dates) - max_records
        for date in dates[:tbd]:
            del self.db[date.strftime("%m-%d-%y")]
        self.persist()
