# Hong Kong Open Data Explorer

See the official Hong Kong 2026–2028 Open Data Plan dataset.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app downloads the official JSON source on first run, saves the dataset as a CSV, and supports searching by Data Provider and keywords.
