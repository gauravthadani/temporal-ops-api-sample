import argparse
import asyncio
import csv
import io
import os
import subprocess
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import httpx
from google.protobuf.timestamp_pb2 import Timestamp
from temporalio.client import CloudOperationsClient
from temporalio.api.cloud.billing.v1 import BillingReportSpec
from temporalio.api.cloud.cloudservice.v1 import (
    CreateBillingReportRequest,
    GetBillingReportRequest,
)

# BillingReportState enum values
BILLING_REPORT_STATE_UNSPECIFIED = 0
BILLING_REPORT_STATE_IN_PROGRESS = 1
BILLING_REPORT_STATE_GENERATED = 2
BILLING_REPORT_STATE_FAILED = 3

SCRIPT_DIR = Path(__file__).parent
DOWNLOAD_DIR = SCRIPT_DIR / "_output"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_billing_month_boundaries(year: int, month: int) -> tuple[Timestamp, Timestamp]:
    """Return (start_inclusive, end_exclusive) for the given billing month in UTC."""
    start_dt = datetime(year, month, 1, tzinfo=timezone.utc)

    if month == 12:
        end_dt = start_dt.replace(year=year + 1, month=1)
    else:
        end_dt = start_dt.replace(month=month + 1)

    start_ts = Timestamp()
    start_ts.FromDatetime(start_dt)
    end_ts = Timestamp()
    end_ts.FromDatetime(end_dt)

    return start_ts, end_ts


async def get_billing_report(api_key: str, namespace: str | None = None):
    # Connect to Temporal Cloud Operations API
    client = await CloudOperationsClient.connect(
        api_key=api_key,
        rpc_metadata={"temporal-cloud-api-version": "v0.12.0"},
    )

    cloud_service = client.cloud_service

    # Build the billing report spec for March 2026
    start_ts, end_ts = get_billing_month_boundaries(2026, 4)
    spec = BillingReportSpec(

        start_time_inclusive=start_ts,
        end_time_exclusive=end_ts,

    )

    print(f"Requesting billing report for {start_ts.ToDatetime()} to {end_ts.ToDatetime()} ...")

    # Step 1: Create a billing report
    create_response = await cloud_service.create_billing_report(
        CreateBillingReportRequest(spec=spec)
    )

    billing_report_id = create_response.billing_report_id
    print(f"Billing report created. ID: {billing_report_id}")

    # Step 2: Poll GetBillingReport until the report is generated (exponential backoff)
    poll_interval = 5
    max_poll_interval = 60

    while True:
        get_response = await cloud_service.get_billing_report(
            GetBillingReportRequest(billing_report_id=billing_report_id)
        )

        report = get_response.billing_report
        state = report.state

        if state == BILLING_REPORT_STATE_GENERATED:
            print("Report generated successfully!")
            break
        elif state == BILLING_REPORT_STATE_FAILED:
            print("ERROR: Billing report generation failed.")
            return
        else:
            state_name = {
                BILLING_REPORT_STATE_UNSPECIFIED: "UNSPECIFIED",
                BILLING_REPORT_STATE_IN_PROGRESS: "IN_PROGRESS",
            }.get(state, f"UNKNOWN({state})")
            print(f"Report state: {state_name} — polling again in {poll_interval}s ...")
            await asyncio.sleep(poll_interval)
            poll_interval = min(poll_interval * 2, max_poll_interval)

    # Step 3: Download the CSV from the first download_info entry
    if not report.download_info:
        print("ERROR: Report generated but no download info available.")
        return

    download = report.download_info[0]
    download_url = download.url
    file_size = download.file_size_bytes

    print(f"Downloading CSV ({file_size} bytes) ...")

    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(download_url)
        resp.raise_for_status()
        csv_content = resp.text

    # Filter by namespace if specified.
    # The CSV ResourceName column has the format "namespace.account_id".
    if namespace:
        reader = csv.DictReader(io.StringIO(csv_content))
        filtered_rows = [
            row for row in reader
            if row.get("ResourceName", "").startswith(f"{namespace}.")
        ]
        if not filtered_rows:
            print(f"WARNING: No billing rows found for namespace '{namespace}'.")

        output_path = DOWNLOAD_DIR / f"billing_report_{namespace}.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)

        print(f"Filtered billing report ({len(filtered_rows)} rows) for namespace '{namespace}' saved to: {output_path}")
    else:
        output_path = DOWNLOAD_DIR / "billing_report.csv"
        output_path.write_text(csv_content)
        print(f"Full billing report saved to: {output_path}")

    html_path = output_path.with_name(output_path.stem + "_dashboard.html")
    dashboard_script = SCRIPT_DIR / "generate_billing_dashboard.py"
    print(f"Generating dashboard: {html_path} ...")
    subprocess.run(
        [sys.executable, str(dashboard_script), str(output_path), str(html_path)],
        check=True,
    )
    webbrowser.open(html_path.as_uri())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Temporal Cloud billing report.")
    parser.add_argument(
        "--namespace",
        help="Filter the report to a specific namespace (e.g. 'production'). "
             "Matches against the ResourceName column prefix.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("TEMPORAL_CLOUD_API_KEY")
    if not api_key:
        print("ERROR: Set the TEMPORAL_CLOUD_API_KEY environment variable.")
        raise SystemExit(1)

    asyncio.run(get_billing_report(api_key=api_key, namespace=args.namespace))