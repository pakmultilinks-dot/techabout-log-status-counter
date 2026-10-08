#!/usr/bin/env python3
"""
Log Status Counter
==================

Counts HTTP status codes in a web server log file.

Reads lines in the common Apache/Nginx "combined" log format, for example:

    203.0.113.7 - - [08/Oct/2026:10:15:32 +0500] "GET /about HTTP/1.1" 200 4521 "-" "Mozilla/5.0"

and reports how many times each status code (200, 301, 404, 500, ...) appears,
plus totals per class (2xx success, 3xx redirect, 4xx client error,
5xx server error). Lines that do not match the log format are counted as
"unparsed" and reported, never silently dropped.

Output formats: human-readable text (default), CSV, or JSON.

Usage:
    python log_status_counter.py sample.log
    python log_status_counter.py sample.log --format json --output result.json
    python log_status_counter.py sample.log --min-count 5   (hide rare codes)

Note: use only sample, public, or generated logs with this script.
Never point it at real server logs containing real user data.

TechAbout Python Developer task 4 - Log Status Counter (ZR-26-00754).
"""

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter

# Combined Log Format: ... "METHOD PATH PROTO" STATUS BYTES "..." "..."
LOG_RE = re.compile(
    r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) [^"]*" (\d{3}) (\S+) "[^"]*" "[^"]*".*$'
)

STATUS_NAMES = {
    200: "OK", 201: "Created", 204: "No Content",
    301: "Moved Permanently", 302: "Found", 304: "Not Modified",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed", 408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error", 502: "Bad Gateway",
    503: "Service Unavailable", 504: "Gateway Timeout",
}

CLASS_NAMES = {
    "2xx": "Success",
    "3xx": "Redirection",
    "4xx": "Client Error",
    "5xx": "Server Error",
    "1xx": "Informational",
}


def parse_line(line):
    """Return the status code int from a log line, or None if unparsable."""
    match = LOG_RE.match(line.strip())
    if not match:
        return None
    return int(match.group(5))


def count_statuses(lines):
    """Return (Counter of status codes, number of unparsed lines)."""
    counter = Counter()
    unparsed = 0
    for line in lines:
        if not line.strip():
            continue
        code = parse_line(line)
        if code is None:
            unparsed += 1
        else:
            counter[code] += 1
    return counter, unparsed


def class_of(code):
    return "%dxx" % (code // 100)


def to_text(counter, unparsed, min_count=1):
    total = sum(counter.values())
    lines = []
    lines.append("HTTP status code counts")
    lines.append("Total requests: %d | Unparsed lines: %d" % (total, unparsed))
    lines.append("")
    lines.append("By status code:")
    for code in sorted(counter):
        if counter[code] < min_count:
            continue
        name = STATUS_NAMES.get(code, "")
        pct = 100.0 * counter[code] / total if total else 0.0
        lines.append("  %d %-22s %6d  (%.1f%%)" %
                     (code, name, counter[code], pct))
    lines.append("")
    lines.append("By class:")
    class_counts = Counter()
    for code, n in counter.items():
        class_counts[class_of(code)] += n
    for cls in sorted(class_counts):
        pct = 100.0 * class_counts[cls] / total if total else 0.0
        lines.append("  %s %-14s %6d  (%.1f%%)" %
                     (cls, CLASS_NAMES.get(cls, ""), class_counts[cls], pct))
    return "\n".join(lines)


def to_csv(counter, unparsed):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["status_code", "name", "class", "class_name", "count"])
    for code in sorted(counter):
        cls = class_of(code)
        writer.writerow([code, STATUS_NAMES.get(code, ""), cls,
                         CLASS_NAMES.get(cls, ""), counter[code]])
    writer.writerow(["unparsed", "", "", "", unparsed])
    return buf.getvalue()


def to_json(counter, unparsed):
    total = sum(counter.values())
    class_counts = Counter()
    for code, n in counter.items():
        class_counts[class_of(code)] += n
    return json.dumps({
        "total_requests": total,
        "unparsed_lines": unparsed,
        "by_status": [
            {"code": code, "name": STATUS_NAMES.get(code, ""),
             "count": counter[code]}
            for code in sorted(counter)
        ],
        "by_class": [
            {"class": cls, "name": CLASS_NAMES.get(cls, ""),
             "count": class_counts[cls]}
            for cls in sorted(class_counts)
        ],
    }, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Count HTTP status codes in a web server log.")
    parser.add_argument("log_file", help="Path to the log file")
    parser.add_argument("--min-count", type=int, default=1,
                        help="Hide status codes with fewer hits (text only)")
    parser.add_argument("--format", choices=["text", "csv", "json"],
                        default="text", help="Output format (default: text)")
    parser.add_argument("--output", default="",
                        help="Write output to this file instead of stdout")
    args = parser.parse_args(argv)

    try:
        with open(args.log_file, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        print("Error: file not found: %s" % args.log_file, file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        with open(args.log_file, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()

    counter, unparsed = count_statuses(lines)

    if args.format == "csv":
        out = to_csv(counter, unparsed)
    elif args.format == "json":
        out = to_json(counter, unparsed)
    else:
        out = to_text(counter, unparsed, args.min_count)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("Counted %d requests, output written to %s"
              % (sum(counter.values()), args.output))
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
