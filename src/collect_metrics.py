"""Export server metrics from Prometheus to a CSV file."""
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

PROM = "http://localhost:9090"

QUERIES = {
    "cpu_pct": '100 - avg by (instance_name) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100',
    "mem_pct": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
    "disk_pct": '(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100',
    "load1": "node_load1",
    "net_rx_kbps": 'sum by (instance_name) (rate(node_network_receive_bytes_total{device!="lo"}[2m])) / 1024',
    "net_tx_kbps": 'sum by (instance_name) (rate(node_network_transmit_bytes_total{device!="lo"}[2m])) / 1024',
}


def query_range(query, start, end, step):
    r = requests.get(
        f"{PROM}/api/v1/query_range",
        params={"query": query, "start": start.timestamp(), "end": end.timestamp(), "step": step},
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    if body["status"] != "success":
        raise RuntimeError(body)
    rows = []
    for series in body["data"]["result"]:
        server = series["metric"].get("instance_name", "unknown")
        for ts, value in series["values"]:
            rows.append((pd.to_datetime(ts, unit="s", utc=True), server, float(value)))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=72, help="how far back to collect")
    parser.add_argument("--step", type=int, default=60, help="seconds between points")
    parser.add_argument("--out", default="data/metrics.csv")
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.hours)
    chunk = timedelta(hours=6)  # small requests, Prometheus limits points per query

    frames = []
    for name, query in QUERIES.items():
        rows, t = [], start
        while t < end:
            rows += query_range(query, t, min(t + chunk, end), args.step)
            t += chunk
        df = pd.DataFrame(rows, columns=["timestamp", "server", name])
        frames.append(df.drop_duplicates(["timestamp", "server"]))

    data = frames[0]
    for df in frames[1:]:
        data = data.merge(df, on=["timestamp", "server"], how="outer")
    data = data.sort_values(["server", "timestamp"]).dropna()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.out, index=False)

    print(f"Saved {len(data)} rows to {args.out}")
    print(data.groupby("server")["timestamp"].agg(["count", "min", "max"]))


if __name__ == "__main__":
    main()
