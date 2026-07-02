# APSystems ECU-3

Custom Home Assistant integration for APSystems ECU-3 gateways using the legacy embedded web interface.

## Features

- Native Home Assistant integration
- Config Flow support
- HACS compatible
- Automatic discovery of:
  - Lifetime generation
  - Daily generation
  - System power
  - Online inverter count
- Individual devices for each micro-inverter
- Per-channel sensors:
  - Power
  - Voltage
  - Frequency
  - Temperature
- Dynamic detection of newly discovered micro-inverters

## Supported hardware

### Supported

- APSystems ECU-3

### Supported firmware

Tested with:

- ECU-3 firmware V3.11.4

This integration relies on the legacy ECU-3 web pages:

- `/cgi-bin/home`
- `/cgi-bin/parameters`

### Not supported

The following products use different communication methods and are **not supported**:

- ECU-R
- ECU-C
- ECU-B

For DS3 systems, existing Home Assistant integrations should be preferred when available.

## Installation

### HACS

1. Open HACS
2. Integrations
3. Custom repositories
4. Add this repository
5. Category: Integration
6. Install
7. Restart Home Assistant

### Manual installation

Copy:

```
custom_components/apsystems_ecu3
```

into:

```
config/custom_components/
```

Restart Home Assistant.

## Configuration

Add a new integration:

```
APSystems ECU-3
```

Configuration parameters:

| Parameter | Description |
|------------|------------|
| IP Address | ECU-3 IP address |
| Polling Interval | Refresh interval in seconds (minimum 60) |
| Inverter Model | YC500, YC500A, YC600, QS1 or Custom |

## Device Structure

### ECU-3 Device

Sensors:

- Lifetime Generation
- Today Generation
- System Power
- Inverters Online
- Firmware Version

### Micro-Inverter Device

One Home Assistant device per micro-inverter.

Sensors:

- A Power
- A Voltage
- A Frequency
- A Temperature

and when available:

- B Power
- B Voltage
- B Frequency
- B Temperature

Additional channels (C/D) are automatically supported.

## Notes

This integration reads data directly from the ECU-3 embedded web server.

No cloud account is required.

No APSystems EMA account is required.

## Diagnostics

Home Assistant diagnostics are supported.

Sensitive information such as:

- IP address
- MAC address

are automatically redacted.

## License

MIT License