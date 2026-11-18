# Modeling Assumptions & Provenance

AirLedger pairs all domain calculations with explicit provenance metadata and confidence ratings.

## 1. Building Physics & Aerosol Dynamics
- **Single-Zone Well-Mixed Box Model**: Assumes room air is sufficiently mixed within each 1-hour time step. (Confidence: `medium`)
- **Natural Particle Deposition Rate ($k$)**: Defaulted to $0.20\,\text{h}^{-1}$ based on empirical indoor aerosol physics literature. (Confidence: `high`)
- **Building Envelope Penetration ($P$)**: Defaulted to $0.70$ for standard construction and $0.35$ for weatherstripped/sealed envelopes. (Confidence: `high`)
- **Air Exchange Rate ($a$)**: Defaulted to $1.0\,\text{ACH}$ for standard rooms and $0.4\,\text{ACH}$ when sealed. (Confidence: `medium`)

## 2. Emission Source Rates
- **Biomass / Chulha Stove**: Nominal emission rate of $450\,\text{mg/h}$ $PM_{2.5}$. (Confidence: `high`)
- **Kerosene Burner**: Nominal emission rate of $120\,\text{mg/h}$. (Confidence: `high`)
- **LPG Gas Cooktop**: Nominal emission rate of $15\,\text{mg/h}$. (Confidence: `high`)
- **Incense Stick / Mosquito Coil**: Smoldering emission rate of $40$–$55\,\text{mg/h}$. (Confidence: `medium`)
- **Kitchen Exhaust Capture**: Operational fan captures $65\%$ of combustion aerosols at the source. (Confidence: `medium`)

## 3. Intervention Ratings
- **Corsi-Rosenthal Box Purifier**: Clean Air Delivery Rate (CADR) of $220\,\text{m}^3/\text{h}$ at estimated ₹2,500 material cost. (Confidence: `high`)
- **Weatherstripping Foam & Draft Guards**: Estimated ₹350 material cost with $35\%$ infiltration reduction. (Confidence: `medium`)
- **N95 Respirators**: $90\%$ particle reduction during transit/outdoor exposure at ₹250 per 5-pack. (Confidence: `high`)

## 4. Atmospheric & Meteorological Data (Open-Meteo API)
- **PM2.5 Ambient Observations**: Fetched via the Open-Meteo Air Quality API (`https://air-quality-api.open-meteo.com/v1/air-quality`) with query parameter `hourly=pm2_5` (unit: $\mu\text{g/m}^3$).
- **Surface Wind Speed**: Fetched via Open-Meteo Weather Forecast API (`https://api.open-meteo.com/v1/forecast`) with query parameter `hourly=wind_speed_10m&wind_speed_unit=kmh` (unit: $\text{km/h}$).
- **Boundary Layer Height**: Documented and available via Open-Meteo Weather Forecast API (`https://api.open-meteo.com/v1/forecast`) with query parameter `hourly=boundary_layer_height` (unit: meters).
- **Coordinate Privacy**: User geolocation coordinates are strictly rounded to 2 decimal places ($\approx 1.1\,\text{km}$ resolution) prior to any outbound transmission or logging.
- **Offline / Stagnation Proxy**: If `boundary_layer_height` is null or unavailable for a grid point, or when operating in offline/sample fallback mode, nocturnal wind stagnation ($\text{wind} < 6\,\text{km/h}$ between 20:00 and 07:00) serves as the diagnostic proxy for thermal inversion.


