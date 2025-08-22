"""Constants for the Legrand Smarther integration."""

# Integration
DOMAIN = "legrand_smarther"
INTEGRATION_NAME = "Legrand Smarther"

# API Configuration
API_BASE_URL = "https://api.developer.legrand.com/smarther/v2.0"
API_TIMEOUT = 30

# OAuth2 Configuration
OAUTH2_AUTHORIZE_URL = "https://developer.legrand.com/oauth/authorize"
OAUTH2_TOKEN_URL = "https://developer.legrand.com/oauth/token"
OAUTH2_SCOPES = ["topology.read", "comfort.read", "comfort.write"]

# Default Configuration
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 300

# Device Types
DEVICE_TYPE_CHRONOTHERMOSTAT = "chronothermostat"

# Thermostat Modes (from API)
THERMOSTAT_MODE_AUTOMATIC = "automatic"
THERMOSTAT_MODE_MANUAL = "manual"
THERMOSTAT_MODE_BOOST = "boost"
THERMOSTAT_MODE_OFF = "off"
THERMOSTAT_MODE_PROTECTION = "protection"

# Thermostat Functions (from API)
THERMOSTAT_FUNCTION_HEATING = "heating"
THERMOSTAT_FUNCTION_COOLING = "cooling"

# Temperature Units
TEMP_UNIT_CELSIUS = "C"

# Error Codes and Messages
ERROR_CODES = {
    400: "Bad request: something is probably wrong in your request body or headers.",
    401: "Unauthorized: user is not authorized to access the requested resource.", 
    404: "Resource not found/Gateway offline: something is probably wrong in your request URL or your thermostat is temporarily disconnected from the network.",
    408: "Request timeout",
    469: "Official application password expired: password used in the Thermostat official app is expired. Please renew it through the official application.",
    470: "Official application terms and conditions expired: terms and conditions for Thermostat official app are expired. Please accept them again through the official application.",
    500: "Server internal error"
}

# User-friendly error messages for UI
USER_ERROR_MESSAGES = {
    401: "Authentication failed. Please re-authenticate.",
    404: "Thermostat is offline or not found. Check your device connection.",
    408: "Request timed out. Please try again.",
    469: "Your Thermostat app password has expired. Please renew it in the official Legrand Thermostat app.",
    470: "Terms and conditions have expired. Please accept them again in the official Legrand Thermostat app.",
    500: "Server error. Please try again later."
}

# Entity Categories
ENTITY_CATEGORY_CONFIG = "config"
ENTITY_CATEGORY_DIAGNOSTIC = "diagnostic"

# Attributes
ATTR_PLANT_ID = "plant_id"
ATTR_MODULE_ID = "module_id"
ATTR_DEVICE_TYPE = "device_type"
ATTR_ACTIVATION_TIME = "activation_time"
ATTR_TEMPERATURE_FORMAT = "temperature_format"
ATTR_LOAD_STATE = "load_state"
ATTR_PROGRAMS = "programs"
ATTR_PROGRAM_NUMBER = "program_number"
ATTR_LAST_UPDATE = "last_update"
ATTR_API_ERROR_CODE = "api_error_code"
ATTR_API_ERROR_MESSAGE = "api_error_message"

# Load States
LOAD_STATE_ACTIVE = "active"
LOAD_STATE_INACTIVE = "inactive"

# Configuration Keys
CONF_MODULES = "modules"
CONF_TEMPERATURE_STEP = "temperature_step"
CONF_ENABLE_EXTRA_SENSORS = "enable_extra_sensors"

# Temperature Steps
TEMP_STEP_HALF = 0.5
TEMP_STEP_TENTH = 0.1