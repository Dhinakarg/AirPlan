"""Domain constants, physical units, and regulatory thresholds for AirLedger."""

from typing import Final

# WHO 24-hour PM2.5 guideline limit (ug/m3)
WHO_PM25_24H_GUIDELINE_UG_M3: Final[float] = 15.0

# Indian National Ambient Air Quality Standard (NAAQS) 24-hour PM2.5 limit (ug/m3)
NAAQS_PM25_24H_LIMIT_UG_M3: Final[float] = 60.0

# Severe smog warning threshold (ug/m3)
SEVERE_SMOG_THRESHOLD_UG_M3: Final[float] = 250.0
