# Repository: kst-sunrise-sunset-csv

Generate Korean-localized (KST, UTC+9) sunrise/sunset CSV files for a given date range and one or more ports in South Korea.  
Outputs per-port CSVs (CP949-encoded) with columns: `시간` (yyyymmdd), `출` (sunrise HH:MM), `몰` (sunset HH:MM), `항` (port).

## Features
- Lightweight SPA-lite solar calculation (no network calls).
- Multiple ports in one run; one CSV per port.
- Filename-safe output: `{START}_{END}_{PORT}.csv`
- CP949 encoding for easy import into Korean Excel.
- Built-in coordinates for major Korean ports (see list below).

## Requirements
- Python 3.9+ (tested with 3.9–3.12)
- pandas

## Quick Start
1) Clone and enter the repo:
```bash
git clone https://github.com/<your-username>/kst-sunrise-sunset-csv.git
cd kst-sunrise-sunset-csv
