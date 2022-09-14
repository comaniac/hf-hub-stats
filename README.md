# Hugging Face Hub Statistics

This simple package provides utilities to analyze Hugging Face hub models.
Speficailly, we now provide the following features:

### Construct a Database for Model Size

For example, the following command calculates the model size (i.e., parameter number)
of the top-1000 most download models in the past 30 days, and dump to a database in JSON format.

```python
python -m hf_hub_stats update_size_db --db size_db.json --end 1000
```

### Constract a Database for Download Trend

The following command extracts the total download count in the past 30 days of top-1000 models,
and dump to a database in JSON format. Since the new record is appended to the database,
suppose we run this command in weekly basis, we can then calculate the weekly download number
and conduct a download trend of each model.

```python
python -m hf_hub_stats update_download_trend_db --db hf_hub_download_trend_db.json --end 1000 
```

### List Top-N Most Download Models

The following command lists top-20 most download models in the past 30 days.

```python
python -m query_top --limit 20
```

In addition, you can also set a range of model sizes. The following command includes
only the model with 1-10B parameters. Providing the model size database can facilitate
the query process by directly using the cached model size.

```python
python -m query_top --limit 20 --min-size 1 --max-size 10 --db size_db.json
```
