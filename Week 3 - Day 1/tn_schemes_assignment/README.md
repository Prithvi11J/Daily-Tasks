# Tamil Nadu Agriculture Government Schemes — Knowledge Graph RAG

Source: https://www.tn.gov.in/scheme_list.php?dep_id=Mg==

The saved official HTML page contains **54 Agriculture – Farmers Welfare Department scheme listings and individual detail-page URLs**. It does **not** include the text of those detail pages. The chatbot therefore distinguishes **listing-only** records from **detail-fetched** records.

## Files

- `app.py`: Streamlit chatbot, NetworkX graph traversal and LangChain grounded answering
- `data/schemes.json`: all 54 scheme names, links and any successfully collected details
- `data/agriculture_listing.html`: original user-supplied government webpage snapshot
- `fetch_details.py`: optional downloader for the 54 official detail pages (polite 1-second pacing)
- `requirements.txt`: dependencies

## Run (Windows CMD)

In your existing `KG RAG Project` folder, activate the Python 3.12 environment:

```cmd
cd "C:\Users\prith\KG RAG Project"
guardrails_venv\Scripts\activate
cd tn_schemes_assignment
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The chatbot works offline with 54 scheme titles and URLs; OpenAI responses require `OPENAI_API_KEY`.

## Optional: fetch all individual scheme descriptions

Stop Streamlit with Ctrl+C, then run:

```cmd
python fetch_details.py
python -m streamlit run app.py
```

The downloader attempts each official detail URL and writes successful text into `data/schemes.json`. Failed detail pages remain `listing_only`. It does not guess missing information. Some pages may be inaccessible or contain JavaScript-driven/PDF content that needs separate extraction. Review extracted records before treating them as authoritative.

## Graph model

```text
Scheme -> LISTED_BY -> Agriculture Department
Scheme -> HAS_EVIDENCE -> Evidence -> LISTED_IN -> Listing URL
Scheme -> HAS_DETAIL_LINK -> Individual scheme URL
Evidence -> CITED_FROM -> Individual URL (only after details are fetched)
```

## Important limitations

- This snapshot includes all **54 scheme links found in the user-provided HTML**, not necessarily every scheme currently published online.
- Eligibility, documents, subsidies and deadlines are *not* available from the listing alone. Only fetched and checked details can substantiate them.
- The optional scraper has not been tested against your local site's responses. If it cannot access detail pages, save them in your browser for offline extraction.
- This is a learning demonstration, not an official government service.
