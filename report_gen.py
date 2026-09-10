#!/usr/bin/env python3
"""
report_gen.py - convert autoscan JSON findings into a color-coded Excel report.

Output:
    <target>_scan_report_<ts>.xlsx

Sheets:
    Summary       - severity counts, per-tool counts, charts, top findings
    <tool>        - one sheet per scanner module with color-coded rows

Severity coloring:
    CRITICAL = red
    HIGH     = orange
    MEDIUM   = yellow
    LOW      = light blue
    INFO     = green
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
SEVERITY_FILL = {
    "CRITICAL": PatternFill("solid", fgColor="C00000"),
    "HIGH":     PatternFill("solid", fgColor="ED7D31"),
    "MEDIUM":   PatternFill("solid", fgColor="FFC000"),
    "LOW":      PatternFill("solid", fgColor="9DC3E6"),
    "INFO":     PatternFill("solid", fgColor="70AD47"),
}
SEVERITY_FONT = {
    "CRITICAL": Font(bold=True, color="FFFFFF"),
    "HIGH":     Font(bold=True, color="FFFFFF"),
    "MEDIUM":   Font(bold=True, color="000000"),
    "LOW":      Font(bold=True, color="000000"),
    "INFO":     Font(bold=True, color="FFFFFF"),
}
HEADER_FILL  = PatternFill("solid", fgColor="305496")
HEADER_FONT  = Font(bold=True, color="FFFFFF")
TITLE_FONT   = Font(bold=True, size=18, color="305496")
SUBTITLE_FONT = Font(italic=True, size=10, color="595959")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# Per-tool parsers: each returns a list of (severity, title, detail)
# ---- Severity heuristics for tools that don't emit severity natively ----
def parse_header(text):
    findings = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("===") or line.startswith("Target:"):
            continue
        m = re.match(r"\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\s+([^:]+):\s*(.*)", line)
        if m:
            sev, name, val = m.group(1), m.group(2).strip(), m.group(3).strip()
            title = f"{name} - {'present' if sev == 'INFO' else 'issue'}"
            detail = val if val else "(no value)"
            findings.append((sev, title, detail))
    return findings

def parse_nmap(text):
    """Pull out open ports + service versions from nmap output."""
    findings = []
    open_re = re.compile(r"^(\d+)\/(\w+)\s+(\w+)\s+(\S+)(?:\s+(.*))?$")
    for line in text.splitlines():
        m = open_re.match(line.strip())
        if m:
            port, proto, state, service, version = m.groups()
            if state == "open":
                sev = "INFO"
                title = f"Port {port}/{proto} open - {service}"
                detail = version or "(version not detected)"
                # bump severity for risky services
                if service in ("telnet", "ftp", "rsh", "rlogin"):
                    sev = "HIGH"
                    detail = f"cleartext legacy protocol: {detail}"
                elif service in ("http-proxy", "ms-sql-s", "mysql", "postgresql"):
                    sev = "MEDIUM"
                findings.append((sev, title, detail))
    # NSE script findings
    for line in text.splitlines():
        if "|_" in line or "| " in line:
            if "VULNERABLE" in line.upper() or "CVE-" in line:
                findings.append(("HIGH", "NSE: potential vulnerability", line.strip()))
    return findings

def parse_nikto(text):
    findings = []
    for line in text.splitlines():
        if "+ " in line and "ERROR" not in line:
            sev = "MEDIUM"
            low = line.lower()
            if any(k in low for k in ("sql injection", "xss", "rce", "remote code", "shell")):
                sev = "CRITICAL"
            elif any(k in low for k in ("vulnerability", "backup", ".git", "config")):
                sev = "HIGH"
            elif "informational" in low or "info" in low:
                sev = "INFO"
            findings.append((sev, "Nikto finding", line.replace("+ ", "").strip()))
    return findings

def parse_whatweb(text):
    findings = []
    # Strip ANSI escape codes
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    # WhatWeb single-line format:
    #   http://target [200 OK] Plugin1, Plugin2[detail], Plugin3, ...
    # or multi-line: PluginName[detail] on its own line
    http_re = re.compile(r"^https?://\S+\s+\[(\d+)\s+(\w+)\](.*)$")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = http_re.match(line)
        if m:
            status, _, payload = m.groups()
            findings.append(("INFO", f"HTTP {status}", "target responded"))
            # parse plugin[detail] pairs separated by ', '
            for part in payload.split(","):
                part = part.strip()
                if not part or "[" not in part:
                    # bare plugin name (no brackets)
                    if part and part.lower() not in ("none",):
                        findings.append(("INFO", "Technology detected", part))
                    continue
                # Split on first '['
                name, _, detail = part.partition("[")
                detail = detail.rstrip("]")
                if name and name.lower() not in ("http", "country", "ip"):
                    findings.append(("INFO", "Technology detected",
                                     f"{name}: {detail}" if detail else name))
            continue
        # multi-line fallback: PluginName[detail]
        for match in re.finditer(r"([A-Za-z][\w/-]*)\[([^\]]*)\]", line):
            name, detail = match.groups()
            if name.lower() in ("http", "country", "ip"):
                continue
            findings.append(("INFO", "Technology detected",
                             f"{name}: {detail}" if detail else name))
    return findings

def parse_wpscan(text):
    findings = []
    for line in text.splitlines():
        low = line.lower()
        if "vulnerable" in low or "cve-" in low or "exploit" in low:
            sev = "CRITICAL" if "exploit" in low else "HIGH"
            findings.append((sev, "WPScan finding", line.strip()))
        elif re.search(r"\[\+|!\]", line):
            sev = "MEDIUM"
            if "outdated" in low: sev = "HIGH"
            findings.append((sev, "WPScan finding", line.strip()))
        elif "WordPress version" in line:
            findings.append(("INFO", "WordPress detected", line.strip()))
    return findings

def parse_dnsenum(text):
    findings = []
    for line in text.splitlines():
        if line.startswith("Name:") or re.match(r"^\S+\.\s+\d+\.\s+IN\s+NS", line):
            findings.append(("INFO", "DNS record", line.strip()))
        if "zone transfer" in line.lower():
            findings.append(("CRITICAL", "DNS zone transfer", line.strip()))
    return findings

def parse_dnsrecon(text):
    findings = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return findings
    for item in data if isinstance(data, list) else []:
        rtype = item.get("type", "")
        if rtype == "AXFR":
            findings.append(("CRITICAL", "Zone transfer successful",
                             f"{item.get('domain','')} -> {item.get('address','')}"))
        elif rtype in ("NS", "MX", "A", "AAAA", "TXT"):
            findings.append(("INFO", f"DNS {rtype}",
                             f"{item.get('domain','')} -> {item.get('address','') or item.get('target','')}"))
        elif rtype == "CNAME":
            findings.append(("INFO", "DNS CNAME",
                             f"{item.get('domain','')} -> {item.get('target','')}"))
    return findings

def parse_harvester(text):
    findings = []
    in_section = None
    for line in text.splitlines():
        low = line.lower()
        if "emails found" in low: in_section = "email"; continue
        if "hosts found" in low: in_section = "host"; continue
        if line.startswith("[-]") or line.startswith("[*]") or line.startswith("[+]"):
            in_section = None; continue
        if in_section == "email" and "@" in line:
            findings.append(("LOW", "Email harvested", line.strip()))
        elif in_section == "host" and line.strip():
            findings.append(("INFO", "Host harvested", line.strip()))
    return findings

def parse_dirb(text):
    findings = []
    for line in text.splitlines():
        if line.startswith("+"):
            sev = "MEDIUM"
            low = line.lower()
            if any(k in low for k in ("admin", "backup", "config", ".git", "sql", "log")):
                sev = "HIGH"
            elif any(k in low for k in ("login", "upload", "phpmyadmin", "wp-")):
                sev = "HIGH"
            findings.append((sev, "Directory/file found", line.replace("+", "").strip()))
    return findings

def parse_gobuster(text):
    findings = []
    for line in text.splitlines():
        if line.startswith("/"):
            sev = "MEDIUM"
            low = line.lower()
            if any(k in low for k in ("admin", "backup", ".git", ".env", "config")):
                sev = "HIGH"
            findings.append((sev, "Path found", line.strip()))
    return findings

def parse_wfuzz(text):
    findings = []
    for line in text.splitlines():
        m = re.match(r"^(\d{3})\s+(\d+)\s+(\d+)\s+(\S+)", line)
        if m and int(m.group(1)) in (200, 301, 302, 403):
            findings.append(("INFO", f"HTTP {m.group(1)} response", m.group(4)))
    return findings

def parse_sqlmap(text):
    findings = []
    for line in text.splitlines():
        low = line.lower()
        if "injectable" in low or "payload" in low:
            sev = "CRITICAL" if "parameter" in low else "HIGH"
            findings.append((sev, "SQLMap finding", line.strip()))
        elif "appears to be" in low and "vulnerable" in low:
            findings.append(("CRITICAL", "SQLi confirmed", line.strip()))
    return findings

PARSERS = {
    "header":     parse_header,
    "nmap":       parse_nmap,
    "nikto":      parse_nikto,
    "whatweb":    parse_whatweb,
    "wpscan":     parse_wpscan,
    "dnsenum":    parse_dnsenum,
    "dnsrecon":   parse_dnsrecon,
    "theharvester": parse_harvester,
    "dirb":       parse_dirb,
    "gobuster":   parse_gobuster,
    "wfuzz":      parse_wfuzz,
    "sqlmap":     parse_sqlmap,
    "raw":        None,   # fallback: no parser, will create a stub sheet
    "jsonfile":   None,
}

# ---------- main ----------

def main(json_path, out_path):
    with open(json_path) as f:
        data = json.load(f)

    target = data["target"]
    started = data.get("started", "")
    finished = data.get("finished", "")
    modules = data.get("modules", [])

    wb = Workbook()
    # remove default sheet, we'll add Summary first explicitly
    wb.remove(wb.active)

    # --------- per-module sheets ---------
    sev_counter = Counter()
    tool_counter = Counter()
    top_findings = []   # for Summary

    for mod in modules:
        mid = mod["id"]
        raw = mod.get("log_snippet", "")
        # Try the raw log file if snippet is empty / too short
        log_file = mod.get("log_file", "")
        if log_file and Path(log_file).exists():
            try:
                raw_text = Path(log_file).read_text(errors="replace")
                # Use full log if it's reasonable size, else snippet
                if len(raw_text) < 200_000:
                    raw = raw_text
            except Exception:
                pass

        parser = PARSERS.get(mod.get("parser", "raw"))
        findings = []
        if parser:
            try:
                findings = parser(raw)
            except Exception as e:
                findings = [("INFO", "Parse error", str(e))]

        # Count by severity & tool
        for sev, title, detail in findings:
            sev_counter[sev] += 1
            tool_counter[mid] += 1
            if sev in ("CRITICAL", "HIGH"):
                top_findings.append((sev, mid, (sev, title, detail)))

        # Write sheet
        ws = wb.create_sheet(title=mid[:31])  # Excel: max 31 chars
        write_module_sheet(ws, mid, mod, findings)

    # --------- summary sheet ---------
    ws = wb.create_sheet("Summary", 0)
    write_summary(ws, target, started, finished, modules, sev_counter, tool_counter, top_findings)

    # save
    wb.save(out_path)
    print(f"Report written: {out_path}")
    print(f"  total findings: {sum(sev_counter.values())}")
    print(f"  by severity:    {dict(sev_counter)}")


def write_module_sheet(ws, mid, mod, findings):
    ws["A1"] = f"Module: {mid}"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = mod.get("description", "")
    ws["A2"].font = SUBTITLE_FONT
    ws["A3"] = f"Command: {mod.get('command','')}"
    ws["A3"].font = SUBTITLE_FONT

    headers = ["Severity", "Title", "Detail"]
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=5, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")
        c.border = BORDER

    row = 6
    for sev, title, detail in findings:
        ws.cell(row=row, column=1, value=sev).fill = SEVERITY_FILL.get(sev, PatternFill())
        ws.cell(row=row, column=1).font = SEVERITY_FONT.get(sev, Font())
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=title)
        ws.cell(row=row, column=3, value=detail)
        for col in range(1, 4):
            ws.cell(row=row, column=col).border = BORDER
            ws.cell(row=row, column=col).alignment = Alignment(
                vertical="top", wrap_text=True
            )
        row += 1

    if not findings:
        ws.cell(row=6, column=1, value="INFO").fill = SEVERITY_FILL["INFO"]
        ws.cell(row=6, column=1).font = SEVERITY_FONT["INFO"]
        ws.cell(row=6, column=2, value="No findings parsed")
        ws.cell(row=6, column=3, value="Tool may have failed, returned no output, or output format not recognized.")

    widths = [12, 35, 90]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 24


def write_summary(ws, target, started, finished, modules, sev_counter, tool_counter, top_findings):
    ws["A1"] = f"Security Scan Report — {target}"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:D1")

    ws["A2"] = f"Started: {started}    Finished: {finished}"
    ws["A2"].font = SUBTITLE_FONT
    ws.merge_cells("A2:D2")

    # KPI tiles - severity counts
    ws["A4"] = "Findings by Severity"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = "Severity"
    ws["B5"] = "Count"
    for c in ("A5", "B5"):
        ws[c].fill = HEADER_FILL
        ws[c].font = HEADER_FONT
        ws[c].border = BORDER

    row = 6
    for sev in SEVERITY_ORDER:
        ws.cell(row=row, column=1, value=sev).fill = SEVERITY_FILL[sev]
        ws.cell(row=row, column=1).font = SEVERITY_FONT[sev]
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=1).border = BORDER
        cnt = ws.cell(row=row, column=2, value=sev_counter.get(sev, 0))
        cnt.font = Font(bold=True)
        cnt.border = BORDER
        cnt.alignment = Alignment(horizontal="center")
        row += 1

    total = sum(sev_counter.values())
    ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=row, column=1).border = BORDER
    ws.cell(row=row, column=2, value=total).font = Font(bold=True)
    ws.cell(row=row, column=2).border = BORDER
    ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")

    # Severity pie chart (sized small to fit tiles)
    pie = PieChart()
    pie.title = "Severity distribution"
    labels = Reference(ws, min_col=1, min_row=6, max_row=6 + len(SEVERITY_ORDER) - 1)
    data   = Reference(ws, min_col=2, min_row=5, max_row=6 + len(SEVERITY_ORDER) - 1)
    pie.add_data(data, titles_from_data=True)
    pie.set_categories(labels)
    pie.dataLabels = DataLabelList(showVal=True)
    pie.height = 9
    pie.width = 14
    ws.add_chart(pie, "D4")

    # Per-tool counts (col A=15)
    base = row + 3
    ws.cell(row=base, column=1, value="Findings by Tool").font = Font(bold=True, size=12)
    ws.cell(row=base + 1, column=1, value="Tool").fill = HEADER_FILL
    ws.cell(row=base + 1, column=1).font = HEADER_FONT
    ws.cell(row=base + 1, column=2, value="Findings").fill = HEADER_FILL
    ws.cell(row=base + 1, column=2).font = HEADER_FONT
    for c in (ws.cell(row=base + 1, column=1), ws.cell(row=base + 1, column=2)):
        c.border = BORDER
        c.alignment = Alignment(horizontal="center")

    r = base + 2
    for mid in modules:
        ws.cell(row=r, column=1, value=mid["id"]).border = BORDER
        cnt = tool_counter.get(mid["id"], 0)
        cell = ws.cell(row=r, column=2, value=cnt)
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center")
        if cnt == 0:
            cell.fill = SEVERITY_FILL["INFO"]
        else:
            cell.fill = SEVERITY_FILL["LOW"]
        r += 1

    # Per-tool bar chart
    bar = BarChart()
    bar.type = "bar"
    bar.title = "Findings by Tool"
    bar.x_axis.title = "Findings"
    bar.y_axis.title = "Tool"
    data_ref = Reference(ws, min_col=2, min_row=base + 1, max_row=r - 1)
    cat_ref  = Reference(ws, min_col=1, min_row=base + 2, max_row=r - 1)
    bar.add_data(data_ref, titles_from_data=True)
    bar.set_categories(cat_ref)
    bar.height = 10
    bar.width = 18
    ws.add_chart(bar, "D" + str(base))

    # Module status table
    base2 = r + 3
    ws.cell(row=base2, column=1, value="Module Status").font = Font(bold=True, size=12)
    headers2 = ["Module", "Status", "Duration (s)", "Findings"]
    for i, h in enumerate(headers2, start=1):
        c = ws.cell(row=base2 + 1, column=i, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.border = BORDER
        c.alignment = Alignment(horizontal="center")

    rr = base2 + 2
    for mid in modules:
        ws.cell(row=rr, column=1, value=mid["id"]).border = BORDER
        rc = mid.get("rc", -1)
        status = "OK" if rc == 0 else ("TIMEOUT" if mid.get("timed_out") else f"ERROR ({rc})")
        sc = ws.cell(row=rr, column=2, value=status)
        sc.border = BORDER
        sc.alignment = Alignment(horizontal="center")
        if "ERROR" in status or "TIMEOUT" in status:
            sc.fill = SEVERITY_FILL["HIGH"] if "ERROR" in status else SEVERITY_FILL["MEDIUM"]
            sc.font = SEVERITY_FONT["HIGH"] if "ERROR" in status else SEVERITY_FONT["MEDIUM"]
        else:
            sc.fill = SEVERITY_FILL["INFO"]
            sc.font = SEVERITY_FONT["INFO"]
        ws.cell(row=rr, column=3, value=mid.get("duration_s", 0)).border = BORDER
        ws.cell(row=rr, column=4, value=tool_counter.get(mid["id"], 0)).border = BORDER
        rr += 1

    # Top findings
    base3 = rr + 3
    ws.cell(row=base3, column=1, value="Top CRITICAL / HIGH findings").font = Font(bold=True, size=12)
    headers3 = ["Severity", "Tool", "Title", "Detail"]
    for i, h in enumerate(headers3, start=1):
        c = ws.cell(row=base3 + 1, column=i, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.border = BORDER
        c.alignment = Alignment(horizontal="center")
    rr = base3 + 2
    for sev, mid, (s, t, d) in sorted(top_findings, key=lambda x: SEVERITY_ORDER.index(x[0]))[:50]:
        sc = ws.cell(row=rr, column=1, value=sev)
        sc.fill = SEVERITY_FILL.get(sev, PatternFill())
        sc.font = SEVERITY_FONT.get(sev, Font())
        sc.border = BORDER
        sc.alignment = Alignment(horizontal="center")
        for col, val in enumerate([mid, t, d], start=2):
            cell = ws.cell(row=rr, column=col, value=val)
            cell.border = BORDER
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        rr += 1

    # Column widths
    widths = [14, 50, 35, 80]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 28


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: report_gen.py <findings.json> <output.xlsx>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
