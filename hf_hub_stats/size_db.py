"""Model Size Database."""
import os
import tempfile

import json
from dataclasses import asdict, dataclass

import transformers
from accelerate import init_empty_weights

MISS_CONFIG_MSG = "does not appear to have a file named config.json"


@dataclass
class CalcModelSizeResult:
    """The dataclass of the result of calculating model size."""

    model_id: str
    size: float

    # Return code
    # 0: valid
    # 1: the model is not supported
    # 2: the model size cannot be estimated without weights
    code: int

    memo: str = None


class SizeDB:
    def __init__(self, file_name):
        self.dirty = False
        self.file_name = file_name
        self.db = {}
        if file_name is not None and os.path.exists(file_name):
            with open(file_name, "r") as filep:
                for key, val in json.load(filep).items():
                    self.db[key] = CalcModelSizeResult(**val)
            print(f"{len(self.db)} record loaded from the model size DB", flush=True)

    def __getitem__(self, key):
        return self.db[key]

    def __contains__(self, key):
        return key in self.db

    def __len__(self):
        return len(self.db)

    def __setitem__(self, key, result):
        model_id = result.model_id
        assert key == model_id

        if model_id in self.db:
            if self.db[model_id] != result:
                print("Update {model_id}")
                self.db[model_id] = result
                self.dirty = True
        else:
            self.db[model_id] = result
            self.dirty = True

    def persist(self):
        if self.file_name is None:
            print("Skip dumping DB because no file path is provided", flush=True)
            return

        if self.dirty:
            print(f"Updating database with total {len(self.db)} records", flush=True)
            with open(self.file_name, "w") as filep:
                data = {k: asdict(v) for k, v in self.db.items()}
                json.dump(data, filep, indent=2)
        self.dirty = False

    def remove_errors(self):
        new_db = {}
        removed = 0
        for model_id, result in self.db.items():
            if result.code == 0:
                new_db[model_id] = result
            else:
                print(f"Remove {model_id} with result: {result}", flush=True)
                removed += 1

        print(f"Removed {removed} models with errors", flush=True)
        self.db = new_db

    def update(self, all_models, args):
        PERSIST_EVERY = 32

        changed = 0
        for model in all_models[args.start : min(args.end, len(all_models))]:
            model_id = model.modelId

            # Cache hit.
            if model_id in self:
                continue

            # Cacht miss. Estimate the model size with empty weights.
            result = get_model_size_in_b_with_empty_weights(model_id, fallback=True)
            self[model_id] = result
            changed += 1

            if changed == PERSIST_EVERY:
                self.persist()

        if changed > 0:
            self.persist()

    def draw_markdown(self, max_memo_len=float("inf")):
        import pandas

        tbl = []
        for key, val in sorted(self.db.items(), key=lambda kv: kv[1].size, reverse=True):
            memo = ""
            if val.code != 0:
                size = "N/A"
                memo = val.memo[: min(max_memo_len, len(val.memo))]
            else:
                if val.size < 1e-6:
                    # < 1K
                    size = "<1K"
                elif val.size < 1e-3:
                    # < 1M
                    size = "{:.0f}K".format(val.size * 1e6)
                elif val.size < 1:
                    size = "{:.0f}M".format(val.size * 1e3)
                else:
                    size = "{:.1f}B".format(val.size)
            tbl.append({"Model": key, "#Parameters": size, "Memo": memo})

        df = pandas.DataFrame.from_dict(tbl)
        print(df.to_markdown(index=False))


def get_model_size_in_b_with_empty_weights(model_id, fallback=True):
    def _get_size_with_empty_weights(model_id):
        cfg = transformers.AutoConfig.from_pretrained(
            model_id, trust_remote_code=True, revision="main"
        )
        try:
            with init_empty_weights():
                model = transformers.AutoModel.from_config(cfg)
            return CalcModelSizeResult(model_id, model.num_parameters() / 1e9, 0)
        except Exception as err:
            if MISS_CONFIG_MSG in str(err):
                return CalcModelSizeResult(model_id, 0, 1, str(err))

        # Failed to estimate without weights. This may due to the fact that
        # the model implementation is not in the official transformers but the model repo.
        return CalcModelSizeResult(model_id, 0, 2)

    def _get_size(model_id):
        try:
            with tempfile.TemporaryDirectory(prefix="hf_hub_stats_model_") as tmpdir:
                model = transformers.AutoModel.from_pretrained(
                    model_id, trust_remote_code=True, cache_dir=tmpdir
                )
                return CalcModelSizeResult(model_id, model.num_parameters() / 1e9, 0)
        except Exception as err:
            # Failed to estimate anyways.
            return CalcModelSizeResult(model_id, 0, 1, str(err))

    result = _get_size_with_empty_weights(model_id)
    if fallback and result.code == 2:
        # Failed to estimate with empty weights. Try again with model on CPU.
        # Note that here we run them sequentially to avoid OOM.
        print(
            f"Getting the size of {model_id} with a pretrained model",
            flush=True,
        )
        result = _get_size(model_id)
        print(f"Result: {result}", flush=True)
    return result
