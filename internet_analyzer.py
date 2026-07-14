#!/usr/bin/env python3
"""
Internet Connection Analyzer
Monitors network connectivity, detects outages, and analyzes root causes.

License: MIT
Repository: https://github.com/Hakitoxx/InternetAnalyzer
"""

import subprocess
import platform
import time
import datetime
import os
import sys
import json
import signal
from collections import deque

# Configuration
PING_HOST = "8.8.8.8"
PING_HOST_SECONDARY = "1.1.1.1"
PING_COUNT = 10
PING_INTERVAL = 5
SUMMARY_INTERVAL = 300
LOG_FILE = "connection_log.txt"
DATA_FILE = "analyzer_data.json"


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


class NetworkAnalyzer:
    def __init__(self):
        self.ping_history = deque(maxlen=1000)
        self.downtime_events = []
        self.current_status = "CONNECTED"
        self.consecutive_fails = 0
        self.total_pings = 0
        self.successful_pings = 0
        self.failed_pings = 0
        self.max_ping = 0
        self.min_ping = float("inf")
        self.avg_ping = 0
        self.start_time = datetime.datetime.now()
        self.gateway = self._detect_gateway()
        self.running = True

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        self.running = False

    def _detect_gateway(self):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                output = result.stdout.decode("utf-8", errors="replace")
                for line in output.split("\n"):
                    if "Default Gateway" in line and ":" in line:
                        gw = line.split(":")[-1].strip()
                        if gw:
                            return gw
            else:
                result = subprocess.run(["ip", "route"], capture_output=True, timeout=10)
                output = result.stdout.decode("utf-8", errors="replace")
                for line in output.split("\n"):
                    if "default via" in line:
                        return line.split("via")[1].split()[0]
        except Exception:
            pass
        return None

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def ping(self, host=PING_HOST):
        try:
            flag = "-n" if platform.system() == "Windows" else "-c"
            timeout_flag = "-w" if platform.system() == "Windows" else "-W"
            flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

            result = subprocess.run(
                ["ping", flag, "1", timeout_flag, "3", host],
                capture_output=True,
                timeout=10,
                creationflags=flags,
            )
            output = result.stdout.decode("utf-8", errors="replace")

            if result.returncode == 0:
                for line in output.split("\n"):
                    if "time=" in line.lower():
                        try:
                            time_part = line.lower().split("time=")[1]
                            ms_str = time_part.split("ms")[0].strip()
                            return float(ms_str)
                        except (IndexError, ValueError):
                            continue
                return 0.0
            return None
        except Exception:
            return None

    def ping_gateway(self):
        if not self.gateway:
            return None
        return self.ping(self.gateway)

    def check_dns(self):
        try:
            import socket
            socket.setdefaulttimeout(3)
            socket.gethostbyname("google.com")
            return True
        except Exception:
            return False

    def check_http(self):
        try:
            import urllib.request
            urllib.request.urlopen("http://httpbin.org/ip", timeout=3)
            return True
        except Exception:
            return False

    def analyze_outage(self):
        reasons = []

        gw_ok = self.ping_gateway()
        if gw_ok is not None:
            reasons.append("Gateway reachable - Router is working")
        else:
            reasons.append("Gateway unreachable - Router issue or local network disconnected")

        dns_ok = self.check_dns()
        if dns_ok:
            reasons.append("DNS resolution working")
        else:
            reasons.append("DNS resolution FAILED - DNS server issue or ISP DNS block")

        ms2 = self.ping(PING_HOST_SECONDARY)
        if ms2 is not None:
            reasons.append(f"Alt DNS (1.1.1.1): {ms2:.0f}ms - Reachable")
        else:
            reasons.append("Alt DNS (1.1.1.1): Unreachable - Possible ISP block")

        http_ok = self.check_http()
        if http_ok:
            reasons.append("HTTP access working")
        else:
            reasons.append("HTTP access FAILED - Firewall or ISP issue")

        if gw_ok is None:
            root = "ROOT CAUSE: Router needs restart or Ethernet cable check"
        elif not dns_ok and not http_ok:
            root = "ROOT CAUSE: ISP-side issue - Contact your provider"
        elif dns_ok and not http_ok:
            root = "ROOT CAUSE: Port/HTTP block - DNS works but connection lost"
        elif not gw_ok:
            root = "ROOT CAUSE: Local network failure - Check router and cables"
        else:
            root = "ROOT CAUSE: Temporary network fluctuation or WiFi dropout - Try 5GHz band"

        reasons.append(root)
        return reasons

    def _update_stats(self, ms):
        self.total_pings += 1
        if ms is not None:
            self.successful_pings += 1
            self.ping_history.append(ms)
            self.consecutive_fails = 0
            if ms > self.max_ping:
                self.max_ping = ms
            if ms < self.min_ping:
                self.min_ping = ms
            if self.ping_history:
                self.avg_ping = sum(self.ping_history) / len(self.ping_history)
        else:
            self.failed_pings += 1
            self.consecutive_fails += 1

    def _format_duration(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        return f"{s}s"

    def _color_for_ping(self, ms):
        if ms is None:
            return Colors.RED
        if ms < 30:
            return Colors.GREEN
        if ms < 80:
            return Colors.GREEN
        if ms < 150:
            return Colors.YELLOW
        return Colors.RED

    def _print_banner(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}")
        print("  +----------------------------------------------------+")
        print("  |          INTERNET CONNECTION ANALYZER               |")
        print("  |          Press Ctrl+C to stop                       |")
        print("  +----------------------------------------------------+")
        print(f"{Colors.RESET}")
        print(f"  Target       : {Colors.CYAN}{PING_HOST}{Colors.RESET} (Google DNS)")
        print(f"  Alt Target   : {Colors.CYAN}{PING_HOST_SECONDARY}{Colors.RESET} (Cloudflare DNS)")
        print(f"  Interval     : {PING_INTERVAL}s ping / {SUMMARY_INTERVAL // 60}m summary")
        print(f"  Log File     : {Colors.DIM}{os.path.abspath(LOG_FILE)}{Colors.RESET}")
        if self.gateway:
            print(f"  Gateway      : {Colors.CYAN}{self.gateway}{Colors.RESET}")
        else:
            print(f"  Gateway      : {Colors.YELLOW}Not detected{Colors.RESET}")
        print()

    def _print_line(self, ms, icon):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        color = self._color_for_ping(ms)
        if ms is not None:
            print(f"  {Colors.DIM}{ts}{Colors.RESET} {icon} {color}{ms:>6.1f} ms{Colors.RESET}")
        else:
            print(f"  {Colors.DIM}{ts}{Colors.RESET} {icon} {Colors.RED}   TIMEOUT{Colors.RESET}")

    def _print_summary(self):
        now = datetime.datetime.now()
        uptime = (now - self.start_time).total_seconds()
        uptime_pct = (self.successful_pings / self.total_pings * 100) if self.total_pings > 0 else 0

        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 56}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  SUMMARY REPORT - {now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 56}{Colors.RESET}")
        print(f"  Duration       : {self._format_duration(uptime)}")
        print(f"  Total Pings    : {self.total_pings}")
        print(f"  Successful     : {Colors.GREEN}{self.successful_pings}{Colors.RESET}")
        print(f"  Failed         : {Colors.RED}{self.failed_pings}{Colors.RESET}")

        pct_color = Colors.GREEN if uptime_pct > 95 else Colors.YELLOW if uptime_pct > 80 else Colors.RED
        print(f"  Uptime         : {pct_color}{uptime_pct:.1f}%{Colors.RESET}")

        if self.min_ping != float("inf"):
            print(f"  Min Latency    : {Colors.GREEN}{self.min_ping:.1f} ms{Colors.RESET}")
            mx_color = Colors.YELLOW if self.max_ping < 200 else Colors.RED
            print(f"  Max Latency    : {mx_color}{self.max_ping:.1f} ms{Colors.RESET}")
            print(f"  Avg Latency    : {Colors.CYAN}{self.avg_ping:.1f} ms{Colors.RESET}")

        recent = list(self.ping_history)[-10:]
        if recent:
            print(f"\n  Last 10 Pings  :", end="")
            for ms in recent:
                c = self._color_for_ping(ms)
                print(f" {c}{ms:.0f}{Colors.RESET}", end="")
            print()

        if self.downtime_events:
            print(f"\n  {Colors.RED}Recent Events:{Colors.RESET}")
            for event in self.downtime_events[-5:]:
                print(f"    {Colors.DIM}{event}{Colors.RESET}")

        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 56}{Colors.RESET}\n")
        self.log(f"SUMMARY - Total:{self.total_pings} OK:{self.successful_pings} Fail:{self.failed_pings} Avg:{self.avg_ping:.1f}ms")

    def _save_data(self):
        try:
            data = {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.datetime.now().isoformat(),
                "total_pings": self.total_pings,
                "successful_pings": self.successful_pings,
                "failed_pings": self.failed_pings,
                "min_ping": self.min_ping if self.min_ping != float("inf") else None,
                "max_ping": self.max_ping,
                "avg_ping": round(self.avg_ping, 2),
                "uptime_pct": round(self.successful_pings / self.total_pings * 100, 2) if self.total_pings else 0,
                "downtime_events": self.downtime_events,
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  {Colors.GREEN}Data saved to {os.path.abspath(DATA_FILE)}{Colors.RESET}")
        except Exception as e:
            print(f"  {Colors.RED}Failed to save data: {e}{Colors.RESET}")

    def run(self):
        self._print_banner()
        self.log("Analyzer started")
        ping_count = 0
        last_summary = time.time()

        try:
            while self.running:
                ping_count += 1
                ms = self.ping()
                self._update_stats(ms)

                if ms is not None:
                    icon = f"{Colors.GREEN}[OK]{Colors.RESET}" if ms < 80 else f"{Colors.YELLOW}[!!]{Colors.RESET}" if ms < 200 else f"{Colors.RED}[!!]{Colors.RESET}"
                else:
                    icon = f"{Colors.RED}[XX]{Colors.RESET}"

                self._print_line(ms, icon)

                if ms is None and self.consecutive_fails >= 3:
                    if self.current_status == "CONNECTED":
                        self.current_status = "OUTAGE"
                        outage_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"\n  {Colors.RED}{Colors.BOLD}!!! CONNECTION LOST - {outage_time} !!!{Colors.RESET}")
                        print(f"  {Colors.YELLOW}Analyzing...{Colors.RESET}\n")

                        reasons = self.analyze_outage()
                        for reason in reasons:
                            print(f"    {Colors.CYAN}>{Colors.RESET} {reason}")
                            self.log(f"OUTAGE: {reason}")

                        self.downtime_events.append(f"{outage_time} - Outage started")
                        print()

                elif ms is not None and self.current_status == "OUTAGE":
                    self.current_status = "CONNECTED"
                    recovery_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n  {Colors.GREEN}{Colors.BOLD}+++ RECONNECTED - {recovery_time} ({ms:.1f}ms) +++{Colors.RESET}\n")
                    self.downtime_events.append(f"{recovery_time} - Reconnected")
                    self.log(f"RECONNECTED - {recovery_time} - Ping: {ms:.1f}ms")

                if time.time() - last_summary >= SUMMARY_INTERVAL:
                    self._print_summary()
                    last_summary = time.time()

                time.sleep(PING_INTERVAL)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n  {Colors.YELLOW}Stopping analyzer...{Colors.RESET}")
            self._print_summary()
            self._save_data()
            self.log("Analyzer stopped")


def main():
    if platform.system() == "Windows":
        os.system("title Internet Analyzer")
        os.system("color 0F")

    analyzer = NetworkAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()
