# Internet Analyzer

A lightweight Python command-line tool for monitoring connectivity, recording latency, detecting outages, and running basic network diagnostics.

## Features

- Continuous ping monitoring
- Primary and secondary connectivity checks
- Automatic default-gateway detection
- DNS resolution checks
- HTTP connectivity checks
- Basic outage diagnostics
- Uptime and latency statistics
- Timestamped event logging
- JSON session-data export
- Windows and Linux support
- No third-party Python dependencies

## How It Works

The analyzer monitors an external target at regular intervals. After repeated failures, it performs additional checks against the local gateway, DNS resolution, a secondary external target, and HTTP connectivity.

```text
Connectivity monitor
        |
        +--> Primary target
        +--> Local gateway
        +--> DNS resolution
        +--> Secondary target
        +--> HTTP check
        +--> Diagnostic summary
```

The diagnostic messages are observations intended to help troubleshoot a connection problem. They are not guaranteed to identify the actual root cause of an outage.

## Requirements

- Python 3.7+
- Windows or Linux
- Standard Python library only

## Usage

```bash
python internet_analyzer.py
```

On Windows, if `run.bat` is present:
```bat
run.bat
```

Press `Ctrl+C` to stop the analyzer. The program writes a final summary and saves session data when it exits.

## Configuration

The main settings are defined near the top of `internet_analyzer.py`:

```python
PING_HOST = "8.8.8.8"
PING_HOST_SECONDARY = "1.1.1.1"
PING_INTERVAL = 5
SUMMARY_INTERVAL = 300
```

## Output Files

| File | Description |
|---|---|
| `connection_log.txt` | Timestamped analyzer and outage events |
| `analyzer_data.json` | Session statistics and recorded downtime events |

## Important Notes

The analyzer relies on external services for connectivity checks. A failed ping or HTTP request can be caused by filtering, firewall rules, routing problems, a temporary service issue, or the target itself being unreachable.

For that reason, the diagnostic result should be treated as a troubleshooting aid rather than a definitive root-cause determination.

## License

MIT License. See [LICENSE](LICENSE) for the full license text.