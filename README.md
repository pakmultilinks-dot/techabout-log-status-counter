# Log Status Counter

A small Python script that counts HTTP status codes in a web server log.
Built for TechAbout task 4 (ZR-26-00754).

## What it does

Given a log file in the common Apache/Nginx "combined" format, it reports:

- How many times each status code appears (200, 301, 404, 500, ...)
  with the standard reason phrase and percentage
- Totals per class: 2xx Success, 3xx Redirection, 4xx Client Error,
  5xx Server Error
- How many lines could not be parsed (reported, never dropped silently)

Lines look like this:

```
203.0.113.7 - - [08/Oct/2026:10:15:32 +0500] "GET /about HTTP/1.1" 200 4521 "-" "Mozilla/5.0"
```

Output formats: `text` (default), `csv`, `json`.

Use only sample, public, or generated logs with this script. Never point
it at real server logs containing real user data.

## Usage

```bash
python log_status_counter.py sample.log
python log_status_counter.py sample.log --min-count 5
python log_status_counter.py sample.log --format json --output result.json
```

## Sample log and result

`generate_sample_log.py` creates a fully **synthetic** log (fixed random
seed, fake TEST-NET IPs, fake paths, plus a few malformed lines). The
included `sample/access.log` has 503 lines; `sample/result.txt` / `.csv` /
`.json` hold the count:

- 500 requests parsed: 391 x 2xx (78.2%), 50 x 3xx (10.0%),
  45 x 4xx (9.0%), 14 x 5xx (2.8%)
- 2 unparsed lines reported

## Tests

```bash
python test_log_status_counter.py
```

9 tests covering valid/invalid line parsing, blank-line handling,
per-code and per-class counting, the min-count filter, and all three
output formats.

## Files

| File | Purpose |
|---|---|
| `log_status_counter.py` | The script |
| `generate_sample_log.py` | Synthetic log generator (seeded, fake data only) |
| `test_log_status_counter.py` | 9 unit tests |
| `sample/access.log` | Synthetic sample log (503 lines) |
| `sample/result.txt` / `.csv` / `.json` | Sample count in three formats |
