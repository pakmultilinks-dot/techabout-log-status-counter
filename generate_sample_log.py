#!/usr/bin/env python3
"""Generate a SYNTHETIC sample web server log (combined log format).

Every line is randomly generated with a fixed seed: fake IPs from the
TEST-NET ranges (never real visitors), fake paths, and a realistic mix of
status codes. A few intentionally malformed lines are included to exercise
the "unparsed" counting. Usage:

    python generate_sample_log.py [num_lines] [output]
"""
import random
import sys

random.seed(20261008)

METHODS = ["GET", "GET", "GET", "GET", "POST", "HEAD"]
PATHS = ["/", "/about", "/services", "/services/web-development",
         "/services/ai-solutions", "/portfolio", "/careers", "/contact",
         "/blog", "/blog/ai-trends-2026", "/assets/css/main.css",
         "/assets/js/app.js", "/assets/img/logo.png", "/favicon.ico",
         "/sitemap.xml", "/robots.txt", "/api/health"]
# (status, weight)
STATUSES = [(200, 82), (201, 2), (301, 4), (302, 2), (304, 3),
            (400, 1), (401, 1), (403, 1), (404, 6), (429, 1),
            (500, 2), (502, 1), (503, 1)]
AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) Safari/605.1",
          "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
          "curl/8.5.0", "Googlebot/2.1"]

STATUS_POOL = [s for s, w in STATUSES for _ in range(w)]


def fake_ip():
    # TEST-NET ranges reserved for documentation: 192.0.2.x, 198.51.100.x
    base = random.choice(["192.0.2", "198.51.100"])
    return "%s.%d" % (base, random.randint(1, 254))


def one_line():
    ip = fake_ip()
    method = random.choice(METHODS)
    path = random.choice(PATHS)
    status = random.choice(STATUS_POOL)
    size = random.randint(200, 60000) if status < 400 else random.randint(150, 3000)
    day = random.randint(1, 7)
    hh = random.randint(0, 23)
    mm = random.randint(0, 59)
    ss = random.randint(0, 59)
    agent = random.choice(AGENTS)
    return ('%s - - [%02d/Oct/2026:%02d:%02d:%02d +0500] "%s %s HTTP/1.1" '
            '%d %d "-" "%s"' % (ip, day, hh, mm, ss, method, path, status, size, agent))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    out = sys.argv[2] if len(sys.argv) > 2 else "sample/access.log"
    lines = [one_line() for _ in range(n)]
    # a few malformed lines to exercise unparsed counting
    lines.insert(100, "this line is not a log line at all")
    lines.insert(250, "203.0.113.9 - - broken [timestamp")
    lines.insert(400, "")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("Wrote %d lines to %s (synthetic data only)" % (len(lines), out))


if __name__ == "__main__":
    main()
