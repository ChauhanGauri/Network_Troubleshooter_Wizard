# 🛠️ Network Troubleshooter Wizard

A terminal-based Python wizard that assists users in diagnosing and resolving common network issues. Built using the `pythondialog` module, it provides an interactive, menu-driven interface for running useful network tests and showing suggestions to fix problems.

---

## 📋 Features

- ✅ Check if you're connected to the internet
- 🌐 View and renew IP configuration
- 📶 Ping tests for connectivity
- 🔍 DNS resolution checks
- 🛰️ Traceroute to track routing issues
- 💡 Displays solutions based on detected problems
- 📜 Clean terminal-based UI using `dialog`

---

## 🧰 Requirements

This tool is built for **Linux** (Debian/Ubuntu-based systems recommended).

### Python Dependencies:
- Python 3.x
- python3-dialog

### System Tools:
- `ping`
- `ifconfig` or `ip`
- `traceroute`
- `dig` or `nslookup`

---

## 🔧 Installation

### 1. Clone this Repository

```bash
git clone https://github.com/yourusername/network-troubleshooter-wizard.git
cd network-troubleshooter-wizard
