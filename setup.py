#!/usr/bin/env python3
"""
setup.py - autoscan dependency installer.

Checks which Kali/open-source tools required by autoscan are present on the
system, and auto-installs the missing ones. Designed to work on Kali (preferred)
and Ubuntu/Debian derivatives. Does NOT run apt-get update/upgrade — that's
the user's choice.

Usage:
    sudo python3 setup.py           # check + install missing
    sudo python3 setup.py --check   # check only, don't install
    sudo python3 setup.py --list    # print the tool list
"""

import argparse
import os
import platform
import subprocess
import sys

# (apt_package, executable_to_check, pip/pipx/gem notes)
# gem packages need Ruby/gem; apt provides the rest on Kali/Ubuntu.
TOOLS = [
    ("nmap",       "nmap",       None),
    ("nikto",      "nikto",      None),
    ("whatweb",    "whatweb",    None),
    ("wpscan",     "wpscan",     "gem: wpscan"),     # ruby gem on kali; apt on some
    ("theharvester","theharvester", None),
    ("dnsrecon",   "dnsrecon",   None),
    ("dnsenum",    "dnsenum",    None),
    ("wfuzz",      "wfuzz",      None),
    ("gobuster",   "gobuster",   None),
    ("dirb",       "dirb",       None),
    ("hydra",      "hydra",      None),
    ("sqlmap",     "sqlmap",     None),
    ("curl",       "curl",       None),
    ("python3",    "python3",    None),
]

# Python deps for the Excel report builder
PYTHON_DEPS = ["openpyxl", "xlsxwriter"]


def have(cmd):
    """Return True if `cmd` is on PATH (or is an absolute path that exists)."""
    import shutil
    return shutil.which(cmd) is not None


def detect_distro():
    """Return (id, codename) e.g. ('kali', 'kali-rolling') or ('ubuntu', 'jammy')."""
    try:
        with open("/etc/os-release") as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v.strip('"').strip("'")
        return data.get("ID", "unknown"), data.get("VERSION_CODENAME", "")
    except FileNotFoundError:
        return ("unknown", "")


def run(cmd, check=True, capture=False):
    """Run a command. If check=True, exit on failure."""
    print(f"  $ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=check,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"  [!] failed (exit {e.returncode})", file=sys.stderr)
        if capture and e.stdout:
            print(e.stdout, file=sys.stderr)
        if check:
            sys.exit(1)
        return e


def check_tools():
    """Return list of (package, exe, install_kind) for missing tools."""
    missing = []
    for pkg, exe, kind in TOOLS:
        if have(exe):
            print(f"  [✓] {exe:14s} present")
        else:
            print(f"  [✗] {exe:14s} MISSING  (install via: {kind or f'apt: {pkg}'})")
            missing.append((pkg, exe, kind))
    return missing


def check_python_deps():
    """Return list of missing python pip packages."""
    missing = []
    for mod in PYTHON_DEPS:
        try:
            __import__(mod)
            print(f"  [✓] python:{mod:12s} present")
        except ImportError:
            print(f"  [✗] python:{mod:12s} MISSING")
            missing.append(mod)
    return missing


def install_apt(packages):
    """Install via apt without running update/upgrade."""
    if not packages:
        return
    print(f"\n[*] Installing via apt: {' '.join(packages)}")
    run(["apt-get", "install", "-y", "--no-install-recommends"] + packages)


def install_gem(packages):
    """Install ruby gems (wpscan)."""
    if not packages:
        return
    for gem in packages:
        print(f"\n[*] Installing gem: {gem}")
        run(["gem", "install", gem, "--no-document"])


def install_pip(packages):
    """Install Python deps via pip3."""
    if not packages:
        return
    print(f"\n[*] Installing python deps: {' '.join(packages)}")
    run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + packages
        if _pip_needs_break()
        else [sys.executable, "-m", "pip", "install"] + packages)


def _pip_needs_break():
    """Return True if the system pip needs --break-system-packages (PEP 668)."""
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--dry-run", "x"],
                       capture_output=True, text=True)
    return "externally-managed-environment" in (r.stderr or "")


def main():
    parser = argparse.ArgumentParser(description="autoscan dependency installer")
    parser.add_argument("--check", action="store_true",
                        help="Check only — do not install anything")
    parser.add_argument("--list", action="store_true",
                        help="Print the list of tools we check for and exit")
    args = parser.parse_args()

    if args.list:
        print("autoscan checks for these tools:")
        for pkg, exe, kind in TOOLS:
            note = f"  ({kind})" if kind else ""
            print(f"  - {exe:14s} apt: {pkg}{note}")
        print("\nPython deps:")
        for m in PYTHON_DEPS:
            print(f"  - {m}")
        sys.exit(0)

    if os.geteuid() != 0 and not args.check:
        print("setup.py must be run as root (sudo) to install packages.", file=sys.stderr)
        print("Re-run with --check if you just want to verify.", file=sys.stderr)
        sys.exit(2)

    distro, codename = detect_distro()
    print(f"[*] Detected OS: {distro} {codename}")
    print(f"[*] autoscan setup — checking dependencies...\n")

    print("[*] System tools:")
    missing_tools = check_tools()
    print("\n[*] Python libraries:")
    missing_py = check_python_deps()

    if args.check:
        if missing_tools or missing_py:
            print(f"\n[!] Missing: {len(missing_tools)} tool(s), {len(missing_py)} python lib(s)")
            sys.exit(1)
        print("\n[✓] All dependencies present.")
        sys.exit(0)

    if not missing_tools and not missing_py:
        print("\n[✓] Everything is already installed. Nothing to do.")
        sys.exit(0)

    print(f"\n[*] Will install: {len(missing_tools)} tool(s), {len(missing_py)} python lib(s)")

    # group missing by install method
    apt_pkgs = [pkg for pkg, _, kind in missing_tools if kind is None]
    gem_pkgs = [pkg for _, exe, kind in missing_tools if kind and kind.startswith("gem:")]
    # Strip the "gem: " prefix for the gem install command
    gem_pkgs = [g.split(":", 1)[1].strip() for g in gem_pkgs]

    if apt_pkgs:
        install_apt(apt_pkgs)
    if gem_pkgs:
        install_gem(gem_pkgs)
    if missing_py:
        install_pip(missing_py)

    # Re-verify
    print("\n[*] Re-checking...")
    still_missing = check_tools()
    still_missing_py = check_python_deps()

    if still_missing or still_missing_py:
        print(f"\n[!] {len(still_missing)} tool(s) and {len(still_missing_py)} python lib(s) still missing.")
        print("    Some tools may not be in your distro's repos. Check the docs.")
        sys.exit(1)

    print("\n[✓] autoscan is ready. Run: ./autoscan.sh")


if __name__ == "__main__":
    main()
