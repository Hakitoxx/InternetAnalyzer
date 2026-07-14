# Internet Analyzer

A lightweight Python tool that monitors your internet connection in real-time, detects outages, and analyzes the root cause.

## Features

- Real-time ping monitoring (Google DNS / Cloudflare DNS)
- Automatic outage detection with root cause analysis
- Gateway, DNS, and HTTP health checks
- Color-coded latency display
- Summary reports every 5 minutes
- Logs and JSON data export
- Works on Windows and Linux

## Usage

### Run directly with Python

```bash
python internet_analyzer.py
```

### Run via batch file (Windows)

Double-click `run.bat` or run it from terminal:

```bash
run.bat
```

## Sample Output

```
  +----------------------------------------------------+
  |          INTERNET CONNECTION ANALYZER               |
  |          Press Ctrl+C to stop                       |
  +----------------------------------------------------+

  14:32:01 [OK]    12.3 ms
  14:32:06 [OK]    14.1 ms
  14:32:11 [OK]    11.8 ms
  14:32:16 [XX]   TIMEOUT

  !!! CONNECTION LOST - 2025-01-15 14:32:16 !!!

    > Gateway unreachable - Router issue or local network disconnected
    > DNS resolution FAILED - DNS server issue or ISP DNS block
    > ROOT CAUSE: Router needs restart or Ethernet cable check
```

## Output Files

| File | Description |
|------|-------------|
| `connection_log.txt` | Timestamped event log |
| `analyzer_data.json` | JSON export of session data |

## Configuration

Edit the top of `internet_analyzer.py` to change settings:

```python
PING_HOST = "8.8.8.8"          # Primary ping target
PING_HOST_SECONDARY = "1.1.1.1" # Secondary ping target
PING_INTERVAL = 5               # Seconds between pings
SUMMARY_INTERVAL = 300          # Seconds between summary reports
```

## Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

## License

MIT License - see [LICENSE](LICENSE) for details.
