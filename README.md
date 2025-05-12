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
git clone https://github.com/yourusername/Network_Troubleshooter_Wizard.git
cd Network_Troubleshooter_Wizard
```
### 2. Install Required Packages

```bash
sudo apt update
sudo apt install python3-dialog net-tools iputils-ping dnsutils traceroute
```


## 🚀 Running the Tool

python3 NTW.py


## ⚙️ Example Use Cases

- You're connected to WiFi but can't open websites

- You're facing DNS errors

- You're trying to debug which hop in the route is failing

- You need a beginner-friendly tool to guide someone through fixing their internet


## 🧪 Troubleshooting

If the script does not work as expected:

- Make sure all dependencies are installed

- Run the script with sudo if a step requires administrative privileges

- Try on a Debian-based system for best compatibility




