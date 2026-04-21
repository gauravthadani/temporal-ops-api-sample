#!/usr/bin/env python3
"""Generate a billing dashboard HTML from a Temporal Cloud billing CSV."""

import csv
import json
import sys
import os
from collections import defaultdict


def load_data(csv_path):
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'namespace':     row['ResourceName'] or '(platform fees)',
                'meter':         row['SKUMeter'],
                'desc':          row['ChargeDescription'],
                'cost':          float(row['ContractedCost'] or 0),
                'qty':           float(row['PricingQuantity'] or 0),
                'unit':          row['PricingUnit'],
                'period_start':  row['ChargePeriodStart'][:10],
                'account':       row['BillingAccountName'],
                'currency':      row['BillingCurrency'],
                'billing_start': row['BillingPeriodStart'][:10],
                'billing_end':   row['BillingPeriodEnd'][:10],
            })
    return rows


def aggregate(rows):
    ns_meter_cost = defaultdict(lambda: defaultdict(float))
    ns_meter_qty  = defaultdict(lambda: defaultdict(float))
    ns_meter_unit = {}
    daily_ns      = defaultdict(lambda: defaultdict(float))

    for r in rows:
        ns_meter_cost[r['namespace']][r['meter']] += r['cost']
        ns_meter_qty[r['namespace']][r['meter']]  += r['qty']
        ns_meter_unit[(r['namespace'], r['meter'])] = r['unit']
        daily_ns[r['period_start']][r['namespace']] += r['cost']

    namespaces  = sorted(ns_meter_cost.keys())
    all_meters  = sorted({m for v in ns_meter_cost.values() for m in v})
    dates       = sorted(daily_ns.keys())
    grand_total = sum(r['cost'] for r in rows) / 100

    # Convert cents -> dollars
    ns_meter_cost_usd = {
        ns: {m: v / 100 for m, v in meters.items()}
        for ns, meters in ns_meter_cost.items()
    }
    daily_usd = {
        d: {ns: v / 100 for ns, v in nv.items()}
        for d, nv in daily_ns.items()
    }

    return {
        'namespaces':    namespaces,
        'all_meters':    all_meters,
        'dates':         dates,
        'grand_total':   grand_total,
        'ns_meter_cost': ns_meter_cost_usd,
        'ns_meter_qty':  {ns: dict(v) for ns, v in ns_meter_qty.items()},
        'ns_meter_unit': {f'{k[0]}|{k[1]}': v for k, v in ns_meter_unit.items()},
        'daily':         daily_usd,
    }


METER_COLORS = {
    'Actions':          ('#3b82f6', 'actions'),
    'Active Storage':   ('#10b981', 'active'),
    'Retained Storage': ('#a855f7', 'retained'),
    'Other':            ('#f59e0b', 'other'),
}
NS_COLORS = ['#6366f1', '#22d3ee', '#f472b6', '#34d399', '#fb923c', '#a78bfa']


def fmt_usd(v):
    return f'${v:,.2f}'


def build_html(rows, agg, meta):
    account       = meta['account']
    billing_start = meta['billing_start']
    billing_end   = meta['billing_end']

    ns_list     = agg['namespaces']
    dates       = agg['dates']
    grand_total = agg['grand_total']
    daily       = agg['daily']

    date_range = f"{billing_start} – {billing_end}"
    short_dates = [d[5:] for d in dates]  # MM-DD

    # --- summary cards ---
    ns_usage_total = sum(
        v for ns, meters in agg['ns_meter_cost'].items()
        if ns != '(platform fees)'
        for v in meters.values()
    )
    platform_total = agg['ns_meter_cost'].get('(platform fees)', {}).get('Other', 0)
    active_ns = [ns for ns in ns_list if ns != '(platform fees)']

    # --- bar chart data (cost by namespace) ---
    ns_totals = {
        ns: sum(agg['ns_meter_cost'][ns].values())
        for ns in ns_list
    }
    max_ns_cost = max(ns_totals.values()) if ns_totals else 1

    def bar_width(cost):
        pct = (cost / max_ns_cost * 100) if max_ns_cost else 0
        return max(pct, 0.01)

    # --- donut chart data ---
    donut_labels = []
    donut_data   = []
    donut_colors = []
    for ns in ns_list:
        for meter, cost in agg['ns_meter_cost'][ns].items():
            label = f'{ns} / {meter}' if ns != '(platform fees)' else f'Enterprise Plan ({meter})'
            donut_labels.append(label)
            donut_data.append(round(cost, 4))
            donut_colors.append(METER_COLORS.get(meter, ('#94a3b8', 'other'))[0])

    # --- stacked bar chart datasets ---
    bar_datasets = []
    for i, ns in enumerate(ns_list):
        color = NS_COLORS[i % len(NS_COLORS)]
        bar_datasets.append({
            'label': ns,
            'data': [round((daily.get(d, {}).get(ns, 0)), 2) for d in dates],
            'backgroundColor': color + 'bf',
            'borderRadius': 4,
            'stack': 'a',
        })

    # --- detail table rows ---
    table_rows_html = ''
    for ns in ns_list:
        for meter, cost in agg['ns_meter_cost'][ns].items():
            qty  = agg['ns_meter_qty'][ns].get(meter, 0)
            unit = agg['ns_meter_unit'].get(f'{ns}|{meter}', '')
            pill_cls = METER_COLORS.get(meter, ('#94a3b8', 'other'))[1]
            table_rows_html += f'''
      <tr>
        <td class="ns">{ns}</td>
        <td class="meter"><span class="pill {pill_cls}">{meter}</span></td>
        <td>{qty:,.4f}</td>
        <td>{unit}</td>
        <td class="cost">{fmt_usd(cost)}</td>
      </tr>'''

    # --- namespace bar rows ---
    ns_bars_html = ''
    for i, ns in enumerate(ns_list):
        cost  = ns_totals[ns]
        color = NS_COLORS[i % len(NS_COLORS)]
        width = bar_width(cost)
        ns_bars_html += f'''
    <div class="bar-row">
      <div class="bar-label">{ns}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{width:.2f}%; background:{color};"></div>
      </div>
      <div class="bar-amount">{fmt_usd(cost)}</div>
    </div>'''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Temporal Cloud Billing Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; padding: 24px; }}
    header {{ margin-bottom: 28px; }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; }}
    header .meta {{ margin-top: 6px; font-size: 0.85rem; color: #94a3b8; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }}
    .card {{ background: #1e2130; border: 1px solid #2d3148; border-radius: 12px; padding: 20px 24px; }}
    .card .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 8px; }}
    .card .value {{ font-size: 1.75rem; font-weight: 700; color: #f8fafc; }}
    .card .value.accent {{ color: #818cf8; }}
    .card .sub {{ font-size: 0.75rem; color: #64748b; margin-top: 4px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }}
    @media (max-width: 800px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
    .panel {{ background: #1e2130; border: 1px solid #2d3148; border-radius: 12px; padding: 24px; }}
    .panel h2 {{ font-size: 0.9rem; font-weight: 600; color: #cbd5e1; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .chart-wrap {{ position: relative; height: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    thead th {{ text-align: left; padding: 8px 12px; color: #64748b; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 1px solid #2d3148; }}
    tbody tr {{ border-bottom: 1px solid #1a1f2e; }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody td {{ padding: 10px 12px; color: #cbd5e1; }}
    tbody td.ns {{ font-family: "SF Mono", "Fira Code", monospace; font-size: 0.8rem; color: #818cf8; }}
    tbody td.cost {{ font-weight: 600; color: #f8fafc; text-align: right; }}
    tbody td.meter {{ color: #94a3b8; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; font-weight: 600; }}
    .pill.actions  {{ background: #1e3a5f; color: #60a5fa; }}
    .pill.active   {{ background: #1a3326; color: #34d399; }}
    .pill.retained {{ background: #2d2233; color: #c084fc; }}
    .pill.other    {{ background: #2a2218; color: #fbbf24; }}
    .bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
    .bar-row:last-child {{ margin-bottom: 0; }}
    .bar-label {{ font-family: "SF Mono", "Fira Code", monospace; font-size: 0.78rem; color: #818cf8; min-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .bar-track {{ flex: 1; background: #0f1117; border-radius: 4px; height: 20px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}
    .bar-amount {{ font-size: 0.8rem; font-weight: 600; color: #f8fafc; min-width: 90px; text-align: right; }}
  </style>
</head>
<body>

<header>
  <h1>Temporal Cloud — Billing Dashboard</h1>
  <div class="meta">
    Account: <strong>{account}</strong> &nbsp;·&nbsp;
    Billing Period: <strong>{date_range}</strong> &nbsp;·&nbsp;
    Data through: <strong>{dates[-1] if dates else 'N/A'}</strong>
  </div>
</header>

<div class="cards">
  <div class="card">
    <div class="label">Total Billed</div>
    <div class="value accent">{fmt_usd(grand_total)}</div>
    <div class="sub">{dates[0] if dates else ''} – {dates[-1] if dates else ''}</div>
  </div>
  <div class="card">
    <div class="label">Active Namespaces</div>
    <div class="value">{len(active_ns)}</div>
    <div class="sub">{', '.join(active_ns) if active_ns else 'none'}</div>
  </div>
  <div class="card">
    <div class="label">Platform Fees</div>
    <div class="value">{fmt_usd(platform_total)}</div>
    <div class="sub">Enterprise Plan</div>
  </div>
  <div class="card">
    <div class="label">Namespace Usage Cost</div>
    <div class="value">{fmt_usd(ns_usage_total)}</div>
    <div class="sub">Actions + Storage</div>
  </div>
</div>

<div class="grid-2">
  <div class="panel">
    <h2>Cost by Namespace</h2>
    {ns_bars_html}
  </div>
  <div class="panel">
    <h2>Cost by SKU Meter</h2>
    <div class="chart-wrap">
      <canvas id="donutChart"></canvas>
    </div>
  </div>
</div>

<div class="grid-2">
  <div class="panel" style="grid-column: 1 / -1;">
    <h2>Daily Cost Trend</h2>
    <div class="chart-wrap" style="height:240px;">
      <canvas id="lineChart"></canvas>
    </div>
  </div>
</div>

<div class="panel">
  <h2>Namespace Breakdown</h2>
  <table>
    <thead>
      <tr>
        <th>Namespace</th>
        <th>Meter</th>
        <th>Quantity</th>
        <th>Unit</th>
        <th style="text-align:right">Cost (USD)</th>
      </tr>
    </thead>
    <tbody>{table_rows_html}
    </tbody>
  </table>
</div>

<script>
const DONUT_LABELS   = {json.dumps(donut_labels)};
const DONUT_DATA     = {json.dumps(donut_data)};
const DONUT_COLORS   = {json.dumps(donut_colors)};
const SHORT_DATES    = {json.dumps(short_dates)};
const BAR_DATASETS   = {json.dumps(bar_datasets)};

new Chart(document.getElementById('donutChart'), {{
  type: 'doughnut',
  data: {{
    labels: DONUT_LABELS,
    datasets: [{{ data: DONUT_DATA, backgroundColor: DONUT_COLORS, borderColor: '#1e2130', borderWidth: 3 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, cutout: '65%',
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#94a3b8', font: {{ size: 11 }}, padding: 14 }} }},
      tooltip: {{ callbacks: {{ label: ctx => ' $' + ctx.parsed.toFixed(2) }} }}
    }}
  }}
}});

new Chart(document.getElementById('lineChart'), {{
  type: 'bar',
  data: {{ labels: SHORT_DATES, datasets: BAR_DATASETS }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }},
      tooltip: {{ callbacks: {{ label: ctx => ' ' + ctx.dataset.label + ': $' + ctx.parsed.y.toFixed(2) }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, grid: {{ color: '#1a1f2e' }} }},
      y: {{ stacked: true, ticks: {{ color: '#64748b', font: {{ size: 10 }}, callback: v => '$' + v }}, grid: {{ color: '#1a1f2e' }} }}
    }}
  }}
}});
</script>

</body>
</html>"""
    return html


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <billing_report.csv> [output.html]")
        sys.exit(1)

    csv_path  = sys.argv[1]
    html_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(csv_path)[0] + '_dashboard.html'

    rows = load_data(csv_path)
    if not rows:
        print("No data found in CSV.")
        sys.exit(1)

    agg  = aggregate(rows)
    meta = {
        'account':       rows[0]['account'],
        'billing_start': rows[0]['billing_start'],
        'billing_end':   rows[0]['billing_end'],
    }

    html = build_html(rows, agg, meta)

    with open(html_path, 'w') as f:
        f.write(html)

    print(f"Dashboard written to: {html_path}")


if __name__ == '__main__':
    main()
