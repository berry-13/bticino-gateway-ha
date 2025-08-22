# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Legrand Smarther v2 Home Assistant integration
- OAuth2 authentication using Legrand Developer API
- Climate entities with full thermostat control
  - Target temperature setting
  - HVAC modes (Off, Heat, Auto)
  - Preset modes (automatic, manual, boost, protection)
- Temperature and humidity sensors with real-time measurements
- Optional binary sensors for heating/cooling state
- Comprehensive error handling for all Legrand API error codes (400, 401, 404, 408, 469, 470, 500)
- Configuration flow with OAuth2 setup and module selection
- Options flow for customizing polling interval and sensor settings
- Diagnostics support for troubleshooting
- Multi-language support (English and Italian)
- HACS compatibility
- Automatic retry logic with exponential backoff for temporary failures
- User-friendly error messages for common issues
- Support for multiple plants and thermostats per account

### Technical Features
- Modern Home Assistant integration patterns
- DataUpdateCoordinator for efficient API polling
- Full async/await implementation
- Type hints throughout codebase
- Comprehensive logging and diagnostics
- OAuth2 token refresh handling
- Entity availability tracking
- Proper device/entity relationships

### Documentation
- Complete setup instructions
- Troubleshooting guide
- Service examples
- Error code reference
- Contributing guidelines

## [Unreleased]

### Planned Features
- Cloud-to-Cloud (C2C) webhooks for real-time updates
- Program list control via select entities
- Additional sensors (update age, trends)
- Enhanced preset mode support
- Improved cooling mode detection

---

**Note**: This integration is unofficial and not affiliated with Legrand Group.