# Open Data Plan Explorer

A Streamlit retrieval-augmented search app for the Hong Kong 2026–2028 Open Data
Plan dataset. It downloads the official JSON source, saves the dataset records
to `data/aodp-new-dataset-list-2026-2028-en.csv`, and lets you search records
by Data Provider or by keywords across the dataset fields. The answer panel
summarizes retrieved rows directly, without inventing information beyond the
source records.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On the first run, the app downloads the source and writes the CSV. Use
**Download latest data from source** to refresh the local CSV. The
**Download dataset CSV** button exports the complete current dataset.

The source is
[aodp-new-dataset-list-2026-2028-en.json](https://resource.data.one.gov.hk/opendata/open-data-list/aodp-new-dataset-list-2026-2028-en.json).
