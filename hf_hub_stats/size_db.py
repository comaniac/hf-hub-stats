"""Model Size Database."""
import concurrent.futures
import os

import json
import shutil
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
        if os.path.exists(file_name):
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
        if self.dirty:
            print(f"Updating database with total {len(self.db)} records", flush=True)
            with open(self.file_name, "w") as filep:
                data = {k: asdict(v) for k, v in self.db.items()}
                json.dump(data, filep, indent=2)
        self.dirty = False

    def update(self, all_models, args):
        BATCH_SIZE = 32

        with concurrent.futures.ThreadPoolExecutor() as executor:
            n_models = len(all_models)
            model_idx = args.start
            while model_idx < n_models:
                futures = []
                while model_idx < n_models and len(futures) < BATCH_SIZE:
                    model = all_models[model_idx]
                    model_id = model.modelId
                    if model_id not in self:
                        futures.append(
                            executor.submit(
                                get_model_size_in_b_with_empty_weights,
                                model_id=model.modelId,
                                fallback=False,
                            )
                        )
                    model_idx += 1
                    if model_idx == args.end:
                        break

                print(
                    f"Collecting results of {len(futures)} tasks. Current model idx {model_idx}",
                    flush=True,
                )
                ids = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    ids.append(result.model_id)
                    if result.code == 2:
                        # Failed to estimate with empty weights. Try again with model on CPU.
                        # Note that here we run them sequentially to avoid OOM.
                        result = get_model_size_in_b_with_empty_weights(
                            result.model_id, fallback=True
                        )

                    self[result.model_id] = result

                self.persist()
                if model_idx >= args.end:
                    break

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


def get_param_in_b(model_id, fallback):
    cfg = transformers.AutoConfig.from_pretrained(model_id, trust_remote_code=True, revision="main")
    try:
        model = transformers.AutoModel.from_config(cfg)
    except Exception as err:
        if MISS_CONFIG_MSG in str(err):
            raise Exception(model_id)

        # This may due to the fact that the model implementation is not in the
        # official transformers but the model repo. In this case, we directly
        # load the pretrained model to calculate the parameter number.
        # This could be slow and need many disk spaces.
        if fallback:
            print(f"Calculating the size of {model_id} with pretrained model on CPU", flush=True)
            model = transformers.AutoModel.from_pretrained(
                cfg, trust_remote_code=True, cache_dir="./temp"
            )
            shutil.rmtree("./temp", ignore_errors=True, onerror=None)
        else:
            # When we are not allowed to load pretrained model (may be in a parallel executor),
            # we simply raise an exception.
            raise RuntimeError(model_id)
    return model.num_parameters() / 1e9


def get_model_size_in_b_with_empty_weights(model_id, fallback=True):
    try:
        with init_empty_weights():
            size_in_b = get_param_in_b(model_id, fallback=fallback)
    except RuntimeError:
        # Failed to estimate without weights and not allowed to fallback.
        return CalcModelSizeResult(model_id, 0, 2)
    except Exception as err:
        # Failed to estimate anyways.
        return CalcModelSizeResult(model_id, 0, 1, str(err))

    return CalcModelSizeResult(model_id, size_in_b, 0)
