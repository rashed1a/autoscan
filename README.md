# Autoscan

An interactive Kali-friendly multi-tool web reconnaissance & vulnerability
scanner. Asks you for a target and a test mode, then orchestrates a curated
set of open-source security tools, captures their findings, and produces a
single color-coded **Excel report** with a Summary sheet, per-tool sheets,
severity counts, and charts.

```
      ___   __  ____________  _____ _________    _   __
     /   | / / / /_  __/ __ \/ ___// ____/   |  / | / /
    / /| |/ / / / / / / / / /\__ \/ /   / /| | /  |/ /
   / ___ / /_/ / / / / /_/ /___/ / /___/ ___ |/ /|  /
  /_/  |_\____/ /_/  \____//____/\____/_/  |_/_/ |_/

   auto recon & vulnerability scanner
   v2.1.0  ·  kali multi-tool orchestrator
   https://rashedtech.com/
```

> **Disclaimer:** Only run this against systems you own or have explicit
> written permission to test. Unauthorized scanning is illegal in most
> jurisdictions and against the ToS of every cloud provider.

**Website:** https://rashedtech.com/

## What it runs

| Module        | Tool              | What it does                                     |
| ------------- | ----------------- | ------------------------------------------------ |
| `header`      | custom (curl)     | Security headers + CSP weakness analysis         |
| `dnsenum`     | dnsenum           | A/MX/NS/TXT records + subdomain brute force      |
| `dnsrecon`    | dnsrecon          | DNS records, brute force, zone transfer test     |
| `theharvester`| theHarvester      | Email + subdomain harvesting (search engines)   |
| `whatweb`     | WhatWeb           | Web technology fingerprinting                    |
| `nmap`        | nmap              | Top-1000 TCP port scan + service/version detect  |
| `nikto`       | Nikto             | Web server vulnerability scan                    |
| `wpscan`      | WPScan            | WordPress vulnerabilities, plugins, users        |
| `dirb`        | dirb              | Directory/file brute force                       |
| `gobuster`    | Gobuster          | Directory brute force (alt)                      |
| `wfuzz`       | wfuzz             | URL/path/parameter fuzzing                       |
| `sqlmap`      | sqlmap            | SQL injection detection                          |

## Quick start

```bash
git clone https://github.com/rashed1a/autoscan.git
cd autoscan

# 1. Install missing tools (only what's needed - does NOT run apt update/upgrade)
sudo python3 setup.py

# 2. Run it - interactive prompts will ask for target + test mode
./autoscan.sh
```

## Requirements

- **OS**: Kali Linux (preferred) or any Debian/Ubuntu derivative. `setup.py` uses `apt-get`.
- **Python**: 3.8+ with `openpyxl` (auto-installed by `setup.py`).
- **Bash**: 4+ (uses `declare -A`, parameter expansion).
- **System**: `curl`, `python3`, standard GNU coreutils. Everything else is installed by `setup.py`.

## Output structure

Each run creates `scan_<target>_<YYYYMMDD>_<HHMMSS>/`:

```
scan_example_com_20260910_143022/
├── findings.json               # structured JSON — fed into report_gen.py
├── example_com_scan_report_20260910_143022.xlsx   # final Excel report
└── raw/                        # one .log + .err per module
    ├── header.log
    ├── header.err
    ├── nmap.log
    ├── nmap.err
    ├── dnsrecon.json            # extra: dnsrecon emits structured JSON too
    ├── cookies.txt              # gray/white-box: Netscape-format session cookies
    ├── login_page.html          # gray-box: captured login form
    └── login_recon.json         # gray-box: detected form fields
```

The `findings.json` is the canonical artifact — the Excel is generated from it. If you want to re-build the Excel with different styling later, run:
```bash
python3 report_gen.py scan_example_com_*/findings.json out.xlsx
```

## Interactive flow

When you run `./autoscan.sh` with no arguments:

```
   ╔══════════════════════════════════════════════════════╗
   ║ ...banner with gradient + 3D panel...               ║
   ╚══════════════════════════════════════════════════════╝

  Target URL (e.g. example.com):
  ▸ example.com

  Test mode — pick one:
    1) Black box   (no credentials, external view)
    2) Gray box    (have a user account, login + authenticated scan)
    3) White box   (you'll provide a session cookie manually)
  ▸ Choice [1/2/3, default 1]: 2

  Gray-box login setup
  Hold on — I'm scanning the site for the login form first.

  [*] Auto-recon: probing https://example.com for login pages...
        [INFO] recon: found login candidate at https://example.com/login (HTTP 200)
        [INFO] recon: form action → https://example.com/auth/login  method: POST
        [INFO] field: name='email' type='text'
        [INFO] field: name='password' type='password'
        [INFO] field: name='csrfmiddlewaretoken' type='hidden'

  [✓] Found login form → https://example.com/login
      form action: https://example.com/auth/login  method: POST
      username field: email
      password field: password
      CSRF field:     csrfmiddlewaretoken (auto-extracted)
  [✓] Using auto-detected settings. Hit Enter to accept them, or type to override.

  Login credentials
  ▸ Username / email: alice@example.com
  ▸ Password: ********

  [✓] Login successful (matched: logout|dashboard|welcome|sign ?out)
```

The recon tries common login paths (`/login`, `/signin`, `/auth/login`,
`/wp-login.php`, `/user/login`, `/account/login`, etc.), parses whatever it
finds, and pre-fills every setting. You only type your credentials — and
a captcha response if one was detected. If the tool can't find a form (rare),
it asks for the URL directly.

Then a live dashboard refreshes as each module runs:

```
  ╔══════════════════════════════════════════════════════╗
  ║ ▸ live status                                       ║
  ╠══════════════════════════════════════════════════════╣
  ║  Target ........ example.com                        ║
  ║  Mode ........... gray                              ║
  ║  Progress ....... 4 / 12                            ║
  ╚══════════════════════════════════════════════════════╝

  [██████████████▱▱▱▱▱▱▱▱▱▱▱] 33%  (4/12 modules)

  ┌─ module progress ──────────────────────────────────┐
  │  ✓  header        OK        8 findings              │
  │  ✓  dnsenum       OK        3 findings              │
  │  ✓  dnsrecon      OK        5 findings              │
  │  ✓  whatweb       OK        7 findings              │
  │  ⏱  nmap          TIMEOUT                           │
  │  …  nikto         running                           │
  └────────────────────────────────────────────────────┘
```

After the run, an Excel report is built.

## Test modes

### Black box (default)
No credentials. External view only. Works against any target.

### Gray box — auto-recon first
The script **auto-discovers the login form** before asking anything. It
probes common login paths, parses the page, and reports back what it found
(login URL, form action, method, all input field names, CSRF token, captcha).
You only type your credentials — and a captcha response if one was detected.

What gets auto-detected:
- Login URL — tries `/login`, `/signin`, `/auth/login`, `/wp-login.php`,
  `/user/login`, `/account/login`, `/log-in`, `/session/new`, etc.
- Form action + method (POST vs GET)
- Username field name (heuristic on `name` attribute: `email`, `username`,
  `login`, `account`, `phone`, etc.)
- Password field (`type="password"`)
- CSRF token (auto-extracted from the login page if the field name matches
  `csrf|xsrf|authenticity|_token|antiforgery`)
- Captcha — both inline `<input name="g-recaptcha-response">` and external
  scripts (reCAPTCHA, hCaptcha, Cloudflare Turnstile)
- 2FA / OTP — detected from page text ("verification code", "two-factor",
  "authenticator")
- OAuth / SSO — page mentions of `Sign in with Google`, etc.

What you type:
- Your credentials (username + password)
- Captcha response value (only if a captcha was detected — solve it in
  your browser, paste the response token)
- 2FA OTP code (only if the first POST response asks for one)
- (Optional) override any auto-detected setting by typing it instead of Enter

If recon can't find a form (rare — JS-only SPA, obscure path), the script
prompts for the URL directly or suggests switching to white-box mode.

**Confirmed to the user** with a status line:
`[✓] Login successful (matched: logout|dashboard|welcome|sign ?out)`

### White box
You paste an authenticated session cookie value (from DevTools → Application →
Cookies). The script writes it into a Netscape-format cookie jar and uses it
for all scans. Most reliable when gray box can't handle the login flow.

## Excel Report Structure

The `.xlsx` has two kinds of sheets:

### `Summary` sheet
- **Title** with target + mode + start/finish timestamps
- **KPI tiles** — findings by severity, color-coded:
  - `CRITICAL` = red
  - `HIGH` = orange
  - `MEDIUM` = yellow
  - `LOW` = light blue
  - `INFO` = green
- **Module status table** — OK / FAIL / TIMEOUT + duration + finding count per tool
- **Pie chart** of severity distribution
- **Bar chart** of findings per tool
- **Top CRITICAL/HIGH findings** list

### Per-tool sheets (`header`, `nmap`, `nikto`, ...)
- Columns: `Severity | Title | Detail`
- Every row color-coded by severity
- Easy to filter / sort in Excel

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `[*] Could not auto-find a login form` | JS SPA, non-standard path, or rate-limited | Script prompts for URL or offers white-box mode |
| Every per-tool sheet says "No findings parsed" | Tool ran but output format wasn't recognized | Check `scan_*/raw/<module>.log` — log format must use `[SEVERITY] title: detail` tags |
| `[✗] Login failed — no session cookie` | Wrong creds, wrong field names, JS-only form, missing CSRF | Switch to `--mode white` and paste a cookie |
| `permission denied: scan_*/raw/` | Ran from a dir you can't write to | `cd` somewhere writable first |
| `nmap: command not found` despite `setup.py` | Running outside Kali, package not in your distro's repos | Install manually: `apt install nmap` or build from source |
| `xlsx file is empty / corrupt` | `openpyxl` not installed | `pip install openpyxl` (or re-run `sudo python3 setup.py`) |
| `[!] excel generation had errors` | JSON is malformed | Run `python3 -m json.tool scan_*/findings.json` to find the error |

## What autoscan does NOT do

Be aware of these gaps before assuming coverage:

- **No authentication bruteforce** — despite `hydra` being installed by `setup.py`, no module currently uses it. Run hydra manually if you need it.
- **No headless browser** — single-page apps that only render their login form after JS execution will fall back to white-box mode.
- **No proxy / WAF evasion** — direct curl/nmap/nikto only. For stealthier scans, route through your own proxy and re-run.
- **No active exploitation** — tools report vulnerabilities, they don't exploit them.
- **No continuous monitoring** — one-shot scans only.
- **No distributed scanning** — runs sequentially. 12 modules × ~minutes each = 10–60 min typical runtime.

## Known limitations

- Tool output parsing is regex-based (see `report_gen.py:PARSERS`). Tools that change their output format in a future version may produce "No findings parsed" sheets.
- The `eval` on line 641 of `autoscan.sh` is intentional (it expands `$mcmd` safely), but be careful when adding modules whose commands include untrusted input.
- The login success check is heuristic — if your app returns a session cookie but no in-body marker, autoscan assumes success.

## Command-line reference

```
./autoscan.sh [flags] [target]

Flags:
  --only a,b,c         Only run these module IDs (comma-separated)
  --skip a,b,c         Skip these module IDs
  --mode black|gray|white   Skip the interactive mode prompt
  --login-url URL      Gray-box: login endpoint
  --user NAME          Gray-box: username/email
  --pass SECRET        Gray-box: password (⚠️ see Security note below)
  --login-success RE   Gray-box: regex that confirms login worked
  -h, --help           Show the usage banner (exits immediately)

If target is omitted, you'll be prompted.
If mode is omitted, you'll be prompted (1=black, 2=gray, 3=white).
```

Examples:

```bash
./autoscan.sh                                       # fully interactive
./autoscan.sh example.com                           # target only, prompt for mode
./autoscan.sh example.com --mode black              # skip both prompts
./autoscan.sh example.com --only header,nmap,nikto  # subset of tools
./autoscan.sh example.com --skip sqlmap,wpscan      # skip slow/dangerous tools
./autoscan.sh example.com --mode gray \
    --login-url https://example.com/login \
    --user alice@example.com --pass 'hunter2' \
    --login-success 'logout|dashboard|welcome'
```

### `--login-success` regex

This is the only flag the script **doesn't** auto-derive for you. After POSTing your
credentials, autoscan greps the response body (and a follow-up GET to the base URL)
for this regex. If it matches, login is considered successful.

Good values:
```bash
# Logged-out words that disappear after login
--login-success 'logout|sign\s?out|log\s?out'

# Logged-in words that appear after login
--login-success 'dashboard|welcome|my account|profile'

# Combine both
--login-success 'logout|dashboard|welcome|sign ?out'
```

It's an ERE (extended regex). If unset, autoscan falls back to "any session cookie named PHPSESSID/JWT/etc." which is usually correct but can produce false positives.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Scan completed (modules may have individual FAILs — check the dashboard) |
| 1 | User error (no target given, login failed, abort) |
| 2 | Bad CLI flag / unknown argument |

Use this in CI:
```bash
./autoscan.sh staging.example.com --mode black --yes
# exit 0 + non-empty findings.json = scan ran
# exit 1 = something fatal happened (rare)
```

## ⚠️ Security note: `--pass` flag

Passing the password via `--pass SECRET` puts it in:
- Your shell history (use `history -d` or a leading space + `HISTCONTROL=ignorespace`)
- `/proc/*/cmdline` while the process is running
- Any process listing (`ps auxe`) on a shared box

**Prefer the interactive prompt** — it uses `read -rs` which doesn't echo the input.

```bash
# Safer: omit --pass, you'll be prompted without echo
./autoscan.sh target.example.com --mode gray --user alice
```

## setup.py — dependency installer

```bash
sudo python3 setup.py           # check + auto-install missing
sudo python3 setup.py --check   # check only (no install, no root)
sudo python3 setup.py --list    # list the tools we check for
```

**Does NOT run `apt-get update` or `apt-get upgrade`.** Those are your
choice. setup.py only installs the missing tools from the autoscan tool
list. Works on Kali (preferred) and Ubuntu/Debian derivatives.

## Adding a new scan module

1. Write `modules/mytool.sh` that prints findings in one of two formats:
   - **Header-tagged** (preferred — auto-parsed by `report_gen.py`):
     ```
     [CRITICAL] some issue: details...
     [HIGH]     another issue: details...
     [INFO]     technology detected: nginx/1.18.0
     ```
   - **Raw** — will land as-is on its own sheet
2. Add a parser function in `report_gen.py` and register it in the `PARSERS` dict
3. Add a row to the `MODULES` array in `autoscan.sh`:
   ```bash
   "mytool|Description here|./modules/mytool.sh $TARGET|raw"
   ```
   The 4th field is the **parser id** that `report_gen.py` will use (`header`, `nmap`,
   `nikto`, `sqlmap`, `wpscan`, `dnsrecon`, `dnsenum`, `theharvester`, `dirb`,
   `gobuster`, `wfuzz`, `whatweb`, or `raw` for no-parsing fallback).
4. Add the package to `setup.py`'s `TOOLS` list so it's auto-installed
5. The `--only` / `--skip` filters use the module id, so users can opt in/out

## License

MIT

## Links

https://rashedtech.com/
