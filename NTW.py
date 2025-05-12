#!/usr/bin/env python3
import subprocess
import re
import os
import sys
import socket
import time

# Check if dialog is installed
try:
    subprocess.run(["which", "dialog"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError:
    print("Dialog is not installed. Installing...")
    try:
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "dialog"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to install dialog. Please install it manually with: sudo apt-get install dialog")
        sys.exit(1)

# Import pythondialog after ensuring dialog is installed
try:
    from dialog import Dialog
except ImportError:
    print("Python dialog module not found. Installing...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pythondialog"], check=True)
        from dialog import Dialog
    except:
        print("Failed to install pythondialog. Please install it manually with: pip install pythondialog")
        sys.exit(1)

# Initialize dialog
d = Dialog(dialog="dialog", autowidgetsize=True)
d.set_background_title("Network Troubleshooter Wizard")

# Function to run shell commands and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=False, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               universal_newlines=True)
        return result.stdout
    except Exception as e:
        return f"Error executing command: {e}"

# Function to get network interfaces
def get_network_interfaces():
    output = run_command("ip -o link show | grep -v 'lo:' | awk -F': ' '{print $2}'")
    return [iface for iface in output.strip().split('\n') if iface]

# Function to get IP configuration
def get_ip_config(interface):
    ip_info = run_command(f"ip addr show {interface}")
    
    # Extract IPv4 address
    ipv4_match = re.search(r'inet\s+([0-9.]+)', ip_info)
    ipv4 = ipv4_match.group(1) if ipv4_match else "Not configured"
    
    # Extract IPv6 address
    ipv6_match = re.search(r'inet6\s+([0-9a-f:]+)', ip_info)
    ipv6 = ipv6_match.group(1) if ipv6_match else "Not configured"
    
    # Extract MAC address
    mac_match = re.search(r'link/ether\s+([0-9a-f:]+)', ip_info)
    mac = mac_match.group(1) if mac_match else "Not available"
    
    return {
        "IPv4": ipv4,
        "IPv6": ipv6,
        "MAC": mac
    }

# Function to check gateway
def check_gateway(interface):
    gateway_info = run_command(f"ip route | grep default | grep {interface}")
    
    if not gateway_info:
        return {"gateway": "Not configured", "reachable": False}
    
    gateway_match = re.search(r'default via\s+([0-9.]+)', gateway_info)
    gateway = gateway_match.group(1) if gateway_match else "Not configured"
    
    if gateway != "Not configured":
        ping_result = run_command(f"ping -c 3 -W 2 {gateway}")
        reachable = "0% packet loss" in ping_result
    else:
        reachable = False
    
    return {"gateway": gateway, "reachable": reachable}

# Function to check DNS resolution
def check_dns(dns_server=None):
    if dns_server:
        dns_check = run_command(f"dig @{dns_server} google.com +short")
    else:
        dns_check = run_command("dig google.com +short")
    
    if dns_check.strip():
        return True
    return False

# Function to get DNS servers
def get_dns_servers():
    dns_info = run_command("cat /etc/resolv.conf | grep nameserver")
    servers = []
    
    for line in dns_info.strip().split('\n'):
        match = re.search(r'nameserver\s+([0-9.]+)', line)
        if match:
            servers.append(match.group(1))
    
    return servers if servers else ["8.8.8.8", "8.8.4.4"]  # Default to Google DNS if none found

# Function to check internet connectivity
def check_internet():
    ping_result = run_command("ping -c 3 -W 2 8.8.8.8")
    if "0% packet loss" in ping_result:
        return True
    return False

# Function to run traceroute
def run_traceroute(target="8.8.8.8"):
    traceroute_result = run_command(f"traceroute -m 15 {target}")
    return traceroute_result

# Function to check UFW status
def check_ufw_status():
    ufw_status = run_command("sudo ufw status")
    
    if "Status: active" in ufw_status:
        status = "Active"
    else:
        status = "Inactive"
    
    rules = []
    for line in ufw_status.strip().split('\n'):
        if "ALLOW" in line or "DENY" in line:
            rules.append(line.strip())
    
    return {"status": status, "rules": rules}

# Function to enable/disable UFW
def toggle_ufw(enable=True):
    if enable:
        run_command("sudo ufw --force enable")
    else:
        run_command("sudo ufw --force disable")

# Function to add UFW rule
def add_ufw_rule(port, protocol, action):
    run_command(f"sudo ufw {action} {port}/{protocol}")

# IP Configuration test
def ip_config_test(interface):
    ip_config = get_ip_config(interface)
    ip_status = f"""Interface: {interface}
MAC Address: {ip_config['MAC']}
IPv4 Address: {ip_config['IPv4']}
IPv6 Address: {ip_config['IPv6']}"""
    
    if ip_config['IPv4'] == "Not configured":
        ip_status += "\n\nWARNING: No IPv4 address configured!"
        ip_status += "\nTry running: sudo dhclient " + interface
    
    code = d.msgbox(f"IP Configuration:\n\n{ip_status}", 15, 60, ok_label="Back")
    return ip_config

# Gateway test
def gateway_test(interface):
    gateway_info = check_gateway(interface)
    
    if gateway_info['gateway'] == "Not configured":
        message = f"Gateway Check:\n\nNo default gateway configured for {interface}.\n\nThis will prevent internet connectivity. Try configuring a gateway."
    elif not gateway_info['reachable']:
        message = f"Gateway Check:\n\nDefault gateway ({gateway_info['gateway']}) is not reachable.\n\nThis indicates a local network issue. Check your router or connection."
    else:
        message = f"Gateway Check:\n\nDefault gateway ({gateway_info['gateway']}) is reachable.\n\nLocal network connection is working properly."
    
    code = d.msgbox(message, 15, 60, ok_label="Back")
    return gateway_info

# DNS test
def dns_test():
    dns_servers = get_dns_servers()
    dns_options = [(server, "") for server in dns_servers]
    dns_options.append(("custom", "Specify a custom DNS server"))
    dns_options.append(("back", "Back to main menu"))
    
    code, dns_choice = d.menu("Select a DNS server to test:",
                            choices=dns_options)
    
    if code != d.OK or dns_choice == "back":
        return None
    
    if dns_choice == "custom":
        code, custom_dns = d.inputbox("Enter a custom DNS server (e.g., 1.1.1.1):")
        if code != d.OK:
            return None
        dns_server = custom_dns
    else:
        dns_server = dns_choice
    
    dns_working = check_dns(dns_server)
    
    if dns_working:
        message = f"DNS Check:\n\nDNS resolution using {dns_server} is working properly.\n\nYou can resolve domain names to IP addresses."
    else:
        message = f"DNS Check:\n\nDNS resolution using {dns_server} is NOT working.\n\nThis will prevent you from accessing websites by name.\n\nTry adding 'nameserver 8.8.8.8' to /etc/resolv.conf"
    
    code = d.msgbox(message, 15, 60, ok_label="Back")
    return {"server": dns_server, "working": dns_working}

# Internet connectivity test
def internet_test():
    internet_working = check_internet()
    
    if internet_working:
        message = "Internet Connectivity:\n\nYou have internet connectivity!\n\nYou can reach external servers."
    else:
        message = "Internet Connectivity:\n\nInternet connectivity test FAILED.\n\nYou cannot reach external servers. Check your router, modem, or ISP."
    
    code = d.msgbox(message, 15, 60, ok_label="Back")
    return internet_working

# Traceroute test
def traceroute_test():
    code, target = d.inputbox("Enter a target to trace (IP or domain):", 
                             init="8.8.8.8")
    
    if code != d.OK:
        return
    
    d.infobox(f"Running traceroute to {target}...\nThis may take a moment.", 
             height=5, width=50)
    
    traceroute_result = run_traceroute(target)
    
    code = d.scrollbox(f"Traceroute to {target}:\n\n{traceroute_result}", 
                      height=20, width=75, title="Traceroute Results", 
                      ok_label="Back")

# UFW management function
def manage_ufw():
    while True:
        ufw_info = check_ufw_status()
        
        choices = [
            ("status", f"UFW Status: {ufw_info['status']}"),
            ("toggle", f"{'Disable' if ufw_info['status'] == 'Active' else 'Enable'} UFW"),
            ("add", "Add a new rule"),
            ("back", "Back to main menu")
        ]
        
        code, choice = d.menu("UFW Firewall Management:", choices=choices)
        
        if code != d.OK or choice == "back":
            break
        
        if choice == "status":
            status_text = f"UFW Status: {ufw_info['status']}\n\n"
            
            if ufw_info['rules']:
                status_text += "Active Rules:\n"
                for rule in ufw_info['rules']:
                    status_text += f"- {rule}\n"
            else:
                status_text += "No active rules found."
            
            d.msgbox(status_text, 20, 70, ok_label="Back")
        
        elif choice == "toggle":
            if ufw_info['status'] == "Active":
                code = d.yesno("Are you sure you want to disable the UFW firewall?", 
                              10, 50, yes_label="Yes", no_label="No")
                if code == d.OK:
                    toggle_ufw(False)
                    d.msgbox("UFW firewall has been disabled.", 10, 50, ok_label="Back")
            else:
                code = d.yesno("Are you sure you want to enable the UFW firewall?", 
                              10, 50, yes_label="Yes", no_label="No")
                if code == d.OK:
                    toggle_ufw(True)
                    d.msgbox("UFW firewall has been enabled.", 10, 50, ok_label="Back")
        
        elif choice == "add":
            # Port input
            code, port = d.inputbox("Enter the port number:", 10, 50)
            if code != d.OK:
                continue
            
            # Protocol selection
            code, protocol = d.menu("Select protocol:",
                                  choices=[("tcp", "TCP"), ("udp", "UDP"), 
                                          ("back", "Cancel")])
            if code != d.OK or protocol == "back":
                continue
            
            # Action selection
            code, action = d.menu("Select action:",
                                choices=[("allow", "Allow"), ("deny", "Deny"), 
                                        ("back", "Cancel")])
            if code != d.OK or action == "back":
                continue
            
            # Add the rule
            add_ufw_rule(port, protocol, action)
            d.msgbox(f"Rule added: {action} {port}/{protocol}", 10, 50, ok_label="Back")

# Main wizard function
def main_wizard():
    # Welcome screen
    d.msgbox("""Welcome to the Network Troubleshooter Wizard!
This tool will guide you through diagnosing and fixing common network issues.
You can choose which tests to run from the main menu.

Let's get started!""", 15, 60)
    
    # Select network interface
    interfaces = get_network_interfaces()
    if not interfaces:
        d.msgbox("No network interfaces found!", 10, 50)
        return
    
    code, interface = d.menu("Select a network interface to troubleshoot:",
                           choices=[(iface, "") for iface in interfaces])
    
    if code != d.OK:
        return
    
    # Store test results
    results = {
        "interface": interface,
        "ip_config": None,
        "gateway": None,
        "dns": None,
        "internet": None
    }
    
    # Main menu loop
    while True:
        choices = [
            ("ip", "Check IP Configuration"),
            ("gateway", "Check Gateway Connectivity"),
            ("dns", "Check DNS Resolution"),
            ("internet", "Check Internet Connectivity"),
            ("traceroute", "Run Traceroute"),
            ("ufw", "Manage UFW Firewall"),
            ("summary", "View Summary Report"),
            ("exit", "Exit Wizard")
        ]
        
        code, choice = d.menu(f"Network Troubleshooter - {interface}",
                            choices=choices)
        
        if code != d.OK or choice == "exit":
            code = d.yesno("Are you sure you want to exit?", 10, 50, 
                          yes_label="Yes", no_label="No")
            if code == d.OK:
                break
            else:
                continue
        
        if choice == "ip":
            results["ip_config"] = ip_config_test(interface)
        
        elif choice == "gateway":
            results["gateway"] = gateway_test(interface)
        
        elif choice == "dns":
            results["dns"] = dns_test()
        
        elif choice == "internet":
            results["internet"] = internet_test()
        
        elif choice == "traceroute":
            traceroute_test()
        
        elif choice == "ufw":
            manage_ufw()
        
        elif choice == "summary":
            # Generate summary based on tests that have been run
            summary = f"Network Troubleshooting Summary for {interface}:\n\n"
            
            if results["ip_config"]:
                summary += f"IP Address: {results['ip_config']['IPv4']}\n"
            else:
                summary += "IP Configuration: Not tested\n"
            
            if results["gateway"]:
                gateway_status = f"{results['gateway']['gateway']} ({'Reachable' if results['gateway']['reachable'] else 'Unreachable'})"
                summary += f"Gateway: {gateway_status}\n"
            else:
                summary += "Gateway: Not tested\n"
            
            if results["dns"]:
                dns_status = f"{results['dns']['server']} ({'Working' if results['dns']['working'] else 'Not Working'})"
                summary += f"DNS: {dns_status}\n"
            else:
                summary += "DNS: Not tested\n"
            
            if results["internet"] is not None:
                summary += f"Internet: {'Connected' if results['internet'] else 'Disconnected'}\n"
            else:
                summary += "Internet: Not tested\n"
            
            ufw_info = check_ufw_status()
            summary += f"Firewall: {ufw_info['status']}\n"
            
            summary += "\nThank you for using the Network Troubleshooter Wizard!"
            
            d.msgbox(summary, 20, 70, ok_label="Back to Menu")

# Main function
if name == "main":
    # Check if running as root
    if os.geteuid() != 0:
        print("This script requires root privileges to access network information and manage firewall.")
        print("Please run with sudo: sudo python3 network_troubleshooter.py")
        sys.exit(1)
    
    try:
        main_wizard()
    except KeyboardInterrupt:
        print("\nExiting Network Troubleshooter Wizard...")
    except Exception as e:
        print(f"An error occurred: {e}")
