# What's Going Around — Local Illness Dashboard

A clean, local **"health weather"** dashboard: current **flu, COVID-19, and RSV**
levels and recent trends for **Eden Prairie / Hennepin County, Minnesota**, built
only from **public health surveillance data** — with every number clearly sourced
and dated.

> Status: **v1**, running on bundled SAMPLE data out of the box. Flip one switch
> to pull live data from CDC. See [Going live](#going-live).

## Why it's built this way (the principles)

These are deliberate and not up for negotiation in v1:

- **Public health data only.** No social-media signals (people misreport) and no
  black-box AI guessing. Just official surveillance you can audit.
- **No personal or health data, from anyone.** No accounts, no logins, no
  tracking. The app never asks a single person about their health.
- **Every number is sourced and dated.** Each value on screen shows where it came
  from, the geography it covers, the date range it covers, and whether it's
  sample or live data.

## What it shows

Three cards — COVID-19, Influenza, RSV — each combining:

| Signal | What it means | Source |
| --- | --- | --- |
| **% of ER visits** | Share of local emergency-room visits for this illness | CDC NSSP (`vutn-jzwm`) |
| **Wastewater activity level** | How much virus is in local sewage (Minimal → Very High) | CDC NWSS (`atcp-73re`) |
| **% flu-like illness (ILINet)** | Classic outpatient flu yardstick (flu card only) | CDC FluView via Delphi Epidata |

Plus a **Sources & methods** section that also links **Minnesota Department of
Health** pages (hospitalizations incl. the 7-county metro / Hennepin, Minnesota
wastewater, and K-12 school outbreaks) as official reference links.

All sources are **public and need no account or API key.**

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

./run.sh                             # or: uvicorn app.main:app --reload
```

Then open **http://localhost:8000**. Auto-generated API docs are at
**http://localhost:8000/docs**, and the raw data is at **/api/dashboard**.

By default you'll see a yellow "SAMPLE data" banner — that's expected; the app
ships with realistic offline sample data so it runs anywhere.

## Going live

Set one environment variable to fetch real data from CDC:

```bash
ILLNESS_LIVE=1 ./run.sh
```

### Verifying the live field names (recommended once)

The dataset identities were cross-checked from multiple sources, but the exact
column names couldn't be byte-verified during development. Confirm them once from
a machine with internet (no key needed) — if anything differs, the field names
are centralized at the top of each `app/sources/*.py` file:

```bash
# CDC NSSP — % of ER visits (the "spine"). Expect fields:
#   week_end, geography, pathogen, percent_visits
curl "https://data.cdc.gov/resource/vutn-jzwm.json?\$limit=1"

# CDC NWSS — wastewater activity level (most uncertain field names).
# List the columns first, then peek at a row:
curl "https://data.cdc.gov/api/views/atcp-73re.json"
curl "https://data.cdc.gov/resource/atcp-73re.json?\$limit=2"

# CDC FluView / ILINet via Delphi Epidata — Minnesota flu-like illness:
curl "https://api.delphi.cmu.edu/epidata/fluview/?regions=mn&epiweeks=202501-202622"
```

To regenerate the sample fixtures after changing the model:

```bash
.venv/bin/python scripts/make_fixtures.py
```

## Localizing to your area

Geography is set per source in `app/config.py`, and **every number on the page
shows the geography it actually covers**, so the three layers are labelled
honestly. With `LOCAL_COUNTY = "Hennepin"`, out of the box you get:

- **Statewide level** — `% of ER visits` for Minnesota (CDC NSSP `vutn-jzwm`).
  CDC publishes this *number* at state level only.
- **Local direction** — CDC's official rising/falling for the Health Service
  Area that contains your county (CDC NSSP `rdmq-nq56`). The HSA name is read
  straight from the data. In the respiratory off-season it may read
  "Not reported locally" — that's CDC's data, not a bug.
- **Local wastewater** — Hennepin County sites (CDC NWSS), with an automatic,
  clearly-noted fall-back to statewide if the live data has no county detail.

To cover a different area, change `LOCAL_COUNTY` (and `STATE_NAME` / `STATE_ABBR`).
You can see exactly what the live API returns for your county with:

```bash
# CDC's local trend rows for your county (shows the HSA name + the trend words):
curl "https://data.cdc.gov/resource/rdmq-nq56.json?\$where=county='Hennepin'&\$order=week_end%20DESC&\$limit=3"

# Confirm CDC wastewater carries county detail for Minnesota:
curl "https://data.cdc.gov/resource/atcp-73re.json?\$limit=2"
```

## Project layout

```
app/
  config.py        Location, the SAMPLE/LIVE switch, and tunables — edit this first.
  models.py        Provenance / Series / Dashboard data classes.
  trends.py        Transparent rising/falling logic + official wastewater buckets.
  cache.py         On-disk cache so LIVE mode is gentle on CDC.
  sources/         One module per feed: cdc_nssp, cdc_wastewater, cdc_ili, mdh.
  aggregate.py     Merges sources into one dashboard payload.
  main.py          FastAPI app: /api/dashboard, /api/health, and the page.
data/fixtures/     Bundled SAMPLE data, shaped like the real API responses.
static/            The dashboard page (no build step, no CDN).
scripts/           make_fixtures.py — regenerates the sample data.
tests/             Runs offline; proves the shape and sourcing are correct.
```

## Tests

```bash
.venv/bin/pytest -q
```

The suite runs entirely on sample data (no network), and checks — among other
things — that **every number on the dashboard carries a source and a date.**

## Roadmap

- **Sharper local geography.** Use CDC sub-state areas and CDC/MDH county-level
  wastewater to refine from "Minnesota" toward Hennepin/Twin Cities specifically.
- **Wire up MDH CSVs.** Add the Minnesota-specific hospitalization, school-outbreak,
  and wastewater downloads as parsed data (currently reference links).
- **Hospitalization severity.** Add CDC RESP-NET rates (`kvib-3txy`).

### Explicitly *not* in scope (parked)

- **Letting people log their own test results.** This requires being older and/or
  working through an organization with parental consent. It is intentionally out
  of scope and not built.

## Data sources & credit

- CDC National Syndromic Surveillance Program (NSSP) — Emergency Department Visits
- CDC National Wastewater Surveillance System (NWSS)
- CDC FluView / ILINet, accessed via the Carnegie Mellon **Delphi Epidata** API
- Minnesota Department of Health (MDH) respiratory surveillance pages

## Disclaimer

This dashboard shows **community-level public health surveillance, not individual
diagnoses**. It is for general awareness only and is **not medical advice**.
