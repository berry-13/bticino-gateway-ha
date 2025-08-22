# Legrand Smarther v2 Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Latest Release](https://img.shields.io/github/release/berry-13/bticino-gateway-ha.svg)](https://github.com/berry-13/bticino-gateway-ha/releases/latest)
[![GitHub All Releases](https://img.shields.io/github/downloads/berry-13/bticino-gateway-ha/total.svg)](https://github.com/berry-13/bticino-gateway-ha/releases)

A Home Assistant custom integration for **Legrand Smarther v2** thermostats using the official Legrand Developer API.

## Features

- **OAuth2 Authentication** - Secure authentication using Legrand's developer portal
- **Climate Control** - Full thermostat control with temperature setpoints, HVAC modes, and preset modes
- **Sensors** - Temperature and humidity sensors with real-time measurements
- **Binary Sensors** - Heating/cooling state indicators
- **Diagnostics** - Built-in diagnostics and error reporting
- **Multi-language Support** - English and Italian translations
- **HACS Compatible** - Easy installation and updates via HACS

## Supported Devices

- Legrand Smarther v2 Chronothermostats
- BTicino Smarther v2 Chronothermostats

## Requirements

1. **Legrand Developer Account** - You need access to the Legrand Developer API
2. **Application Credentials** - OAuth2 client ID and secret from Legrand
3. **Home Assistant 2023.11+** - Required for modern OAuth2 support

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/berry-13/bticino-gateway-ha`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Legrand Smarther" and install

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/berry-13/bticino-gateway-ha/releases)
2. Extract the zip file
3. Copy the `custom_components/legrand_smarther` folder to your `config/custom_components/` directory
4. Restart Home Assistant

## Setup

### 1. Legrand Developer Portal Setup

1. Go to the [Legrand Developer Portal](https://developer.legrand.com/)
2. Create an account or log in
3. Create a new application for Home Assistant integration
4. Note down your **Client ID** and **Client Secret**
5. Set the redirect URI to: `https://my.home-assistant.io/redirect/oauth`

### 2. Application Credentials Configuration

Before adding the integration, you need to configure application credentials:

1. Go to **Settings** → **Devices & Services** → **Application Credentials**
2. Click **Add Application Credential**
3. Choose **Legrand Smarther** from the list
4. Enter your **Client ID** and **Client Secret** from the Legrand Developer Portal
5. Click **Submit**

### 3. Integration Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Legrand Smarther**
4. Follow the OAuth2 authentication flow
5. Select which thermostats you want to add
6. Configure options like polling interval and additional sensors

## Configuration Options

The integration provides several configuration options accessible via **Configure** in the integration settings:

- **Polling Interval** (30-300 seconds) - How often to poll the API for updates
- **Temperature Step** (0.1°C or 0.5°C) - Temperature adjustment increment
- **Enable Extra Sensors** - Additional diagnostic sensors (setpoint, last update, heating/cooling state)

## Entities Created

For each thermostat, the integration creates:

### Climate Entity
- **Entity ID**: `climate.{thermostat_name}_climate`
- **Features**: Target temperature, HVAC modes (Off, Heat, Auto), preset modes (automatic, manual, boost, protection)
- **Attributes**: Current/target temperature, humidity, heating state, program info

### Temperature Sensor
- **Entity ID**: `sensor.{thermostat_name}_temperature`
- **Device Class**: Temperature
- **Unit**: °C
- **Updates**: Real-time temperature readings from the thermostat

### Humidity Sensor
- **Entity ID**: `sensor.{thermostat_name}_humidity`
- **Device Class**: Humidity
- **Unit**: %
- **Updates**: Real-time humidity readings from the thermostat

### Optional Diagnostic Sensors (if enabled)
- **Setpoint Sensor**: Current target temperature setting
- **Last Update Sensor**: Timestamp of last successful update
- **Heating Binary Sensor**: Whether heating is currently active
- **Cooling Binary Sensor**: Whether cooling is currently active

## Error Handling

The integration provides comprehensive error handling for all Legrand API error codes:

| Error Code | Description | User Action |
|------------|-------------|-------------|
| 401 | Authentication failed | Re-authenticate in integration settings |
| 404 | Thermostat offline/not found | Check device connection |
| 408 | Request timeout | Automatic retry with backoff |
| 469 | Thermostat app password expired | Renew password in official Legrand app |
| 470 | Terms and conditions expired | Accept terms in official Legrand app |
| 500 | Server error | Automatic retry with backoff |

## Services

The integration works with standard Home Assistant climate services:

```yaml
# Set temperature
service: climate.set_temperature
target:
  entity_id: climate.living_room_climate
data:
  temperature: 21.5

# Set HVAC mode
service: climate.set_hvac_mode
target:
  entity_id: climate.living_room_climate
data:
  hvac_mode: heat

# Set preset mode
service: climate.set_preset_mode
target:
  entity_id: climate.living_room_climate
data:
  preset_mode: boost
```

## Troubleshooting

### Authentication Issues
- Verify your Legrand Developer account has the required permissions
- Check that your application credentials are correctly configured
- Ensure the redirect URI is set correctly in the Legrand Developer Portal

### Device Not Found (404 Errors)
- Check that your thermostat is online and connected to the network
- Verify the device is properly configured in the Legrand/BTicino app
- Ensure your Legrand account has access to the device

### API Rate Limiting
- Increase the polling interval in integration options
- The integration includes automatic retry logic for temporary failures

### Official App Issues (469/470 Errors)
- Open the official Legrand Thermostat or BTicino app
- Renew your password or accept updated terms and conditions
- These errors require action in the official app, not Home Assistant

## Development

This integration is built following Home Assistant's modern integration patterns:

- **OAuth2 Flow** with application credentials
- **DataUpdateCoordinator** for efficient polling
- **Async/await** throughout for performance
- **Type hints** for better code quality
- **Comprehensive error handling** with user-friendly messages
- **Diagnostics support** for troubleshooting

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration. Legrand and BTicino are trademarks of Legrand Group. This integration is not affiliated with or endorsed by Legrand.

## Support

- **Issues**: [GitHub Issues](https://github.com/berry-13/bticino-gateway-ha/issues)
- **Discussions**: [GitHub Discussions](https://github.com/berry-13/bticino-gateway-ha/discussions)
- **Home Assistant Community**: [Home Assistant Forum](https://community.home-assistant.io/)