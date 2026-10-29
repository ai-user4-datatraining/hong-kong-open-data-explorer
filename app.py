import csv
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DATA_URL = (
    "https://resource.data.one.gov.hk/opendata/open-data-list/"
    "aodp-new-dataset-list-2026-2028-en.json"
)
CSV_PATH = Path(__file__).parent / "data" / "aodp-new-dataset-list-2026-2028-en.csv"
USER_AGENT = "Mozilla/5.0 (compatible; OpenDataPlanExplorer/1.0)"


def download_dataset(url: str = DATA_URL) -> tuple[dict[str, Any], list[dict[str, str]]]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("The source JSON does not contain a valid 'data' list.")
    if any(not isinstance(row, dict) for row in payload["data"]):
        raise ValueError("The source JSON contains a dataset entry that is not an object.")

    records = [
        {
            str(key): "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in payload["data"]
    ]
    metadata = {key: value for key, value in payload.items() if key != "data"}
    return metadata, records


def records_to_csv(records: list[dict[str, str]]) -> str:
    fieldnames = list(dict.fromkeys(key for record in records for key in record))
    if not fieldnames:
        return ""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def save_records(records: list[dict[str, str]], path: Path = CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(records_to_csv(records), encoding="utf-8-sig", newline="")


def load_records(path: Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def refresh_dataset(
    path: Path = CSV_PATH,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    metadata, records = download_dataset()
    save_records(records, path)
    return metadata, records


def retrieve_records(
    records: list[dict[str, str]],
    provider: str = "All",
    query: str = "",
) -> list[dict[str, str]]:
    provider_matches = [
        record
        for record in records
        if provider == "All" or record.get("Data Provider", "") == provider
    ]
    terms = re.findall(r"\w+", query.casefold(), flags=re.UNICODE)
    if not terms:
        return provider_matches

    ranked: list[tuple[int, int, dict[str, str]]] = []
    for index, record in enumerate(provider_matches):
        searchable_text = " ".join(record.values()).casefold()
        score = sum(searchable_text.count(term) for term in terms)
        if score:
            ranked.append((score, index, record))

    ranked.sort(key=lambda result: (-result[0], result[1]))
    return [record for _, _, record in ranked]


def build_answer(
    records: list[dict[str, str]], provider: str, query: str
) -> str:
    if not records:
        return "No matching dataset records were found. Try a broader query or provider."

    provider_label = provider if provider != "All" else "all providers"
    intro = f"Found {len(records)} dataset record(s) for {provider_label}."
    if query.strip():
        intro += f' Matches for "{query.strip()}":'
    else:
        intro += " Here are the available records:"

    lines = [intro]
    for record in records[:10]:
        name = record.get("Name of Dataset", "Unnamed dataset")
        release = record.get("Target Release Date", "Not specified")
        lines.append(f"- {name} (target release: {release})")
    if len(records) > 10:
        lines.append(f"- Showing the first 10 of {len(records)} matching records.")
    return "\n".join(lines)


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Hong Kong Open Data Explorer", page_icon="📊", layout="wide")
    st.markdown(
        "<style>h1 { color: #d32f2f; }</style>",
        unsafe_allow_html=True,
    )
    st.title("Hong Kong Open Data Explorer")
    st.caption(
        "Search planned open datasets from the Hong Kong 2026–2028 Open Data Plan. "
        "Answers are grounded in the retrieved source records."
    )

    if "records" not in st.session_state:
        if CSV_PATH.exists():
            st.session_state.records = load_records()
        else:
            try:
                metadata, records = refresh_dataset()
                st.session_state.records = records
                st.session_state.metadata = metadata
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
                st.error(f"Could not download the source dataset: {error}")
                st.stop()

    if st.button("Download latest data from source"):
        try:
            metadata, records = refresh_dataset()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            st.error(f"Could not refresh the source dataset: {error}")
        else:
            st.session_state.records = records
            st.session_state.metadata = metadata
            st.success(f"Saved {len(records)} records to {CSV_PATH}.")

    records = st.session_state.records
    providers = sorted(
        {record.get("Data Provider", "") for record in records if record.get("Data Provider")}
    )
    with st.sidebar:
        st.header("Search")
        provider = st.selectbox("Data Provider", ["All", *providers])
        query = st.text_input(
            "Ask about datasets",
            placeholder="e.g. Which datasets cover population?",
        )

    results = retrieve_records(records, provider, query)
    st.subheader("Answer")
    st.write(build_answer(results, provider, query))

    st.subheader("Retrieved source records")
    st.caption(f"{len(results)} matching record(s)")
    st.dataframe(results, hide_index=True, width="stretch")

    st.download_button(
        "Download dataset CSV",
        data=records_to_csv(records).encode("utf-8-sig"),
        file_name=CSV_PATH.name,
        mime="text/csv",
    )
    if CSV_PATH.exists():
        st.caption(f"Local CSV: `{CSV_PATH}`")
    metadata = st.session_state.get("metadata", {})
    if metadata.get("As of Date"):
        st.caption(f"Source data as of {metadata['As of Date']}.")


if __name__ == "__main__":
    main()
