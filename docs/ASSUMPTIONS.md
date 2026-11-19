# AirPlan Modeling Assumptions & Domain Constant Provenance

This document records the physical meaning, literature rationale, and confidence rating for every domain factor in [app/constants.py](../app/constants.py), followed by verified findings from the Open-Meteo meteorological API integration audit.

---

## 1. Domain Constants in `app/constants.py`

Every constant carries an explicit physical unit, documented provenance, and confidence rating (`high`, `medium`, or `low`).

### A. Air Quality Regulatory Thresholds ($\mu\text{g/m}^3$)

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `WHO_PM25_24H_GUIDELINE_UG_M3` | `15.0` | $\mu\text{g/m}^3$ | `high` | World Health Organization (WHO) 2021 Global Air Quality Guideline for 24-hour mean $PM_{2.5}$ exposure. Benchmark for long-term health protection. |
| `NAAQS_PM25_24H_LIMIT_UG_M3` | `60.0` | $\mu\text{g/m}^3$ | `high` | Central Pollution Control Board (CPCB) Indian National Ambient Air Quality Standard (NAAQS) 24-hour ceiling for residential areas. |
| `SEVERE_SMOG_THRESHOLD_UG_M3` | `250.0` | $\mu\text{g/m}^3$ | `high` | CPCB "Severe" pollution threshold and Graded Response Action Plan (GRAP Stage-IV) trigger level in Delhi-NCR. |

---

### B. Building Infiltration Factors by Leakiness (Dimensionless Ratio, $0\text{--}1$)

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `INFILTRATION_TIGHT` | `0.35` | scalar | `high` | Ratio of indoor-to-outdoor particulate concentration in well-sealed structures with weatherstripped doors, modern window gaskets, and closed fenestration. |
| `INFILTRATION_AVERAGE` | `0.60` | scalar | `medium` | Empirical indoor/outdoor ratio for typical Indian urban masonry apartments with standard loose-fitting wooden doors and unsealed windows. |
| `INFILTRATION_LEAKY` | `0.85` | scalar | `high` | Ratio for highly ventilated or unsealed structures (e.g. open jali screens, warped doors, unbaffled ventilators), where indoor concentration closely tracks outdoor ambient smog. |

---

### C. Active Domestic Mitigation Multipliers (Dimensionless, $0\text{--}1$)

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `PURIFIER_FACTOR` | `0.30` | scalar | `high` | Multiplier applied to indoor infiltrated particulates when an active HEPA or Corsi-Rosenthal box air cleaner is running in a closed room. Corresponds to a $\approx 70\%$ steady-state mass reduction under realistic residential air exchange rates. |
| `OPEN_WINDOW_FACTOR` | `0.90` | scalar | `high` | Multiplier applied during hours when windows are actively opened. Near-complete equilibrium ($90\%$) with ambient outdoor air is established within minutes due to rapid natural ventilation. |

---

### D. Commute & Transit Microenvironment Multipliers (Dimensionless)

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `MODE_FACTOR_WALK` | `1.0` | scalar | `high` | Direct outdoor pedestrian exposure; multiplier equal to ambient monitor readings. |
| `MODE_FACTOR_CYCLE` | `1.0` | scalar | `high` | Roadside cycling exposure; equal to ambient outdoor concentration (physiological exertion handled separately via elevated breathing rate). |
| `MODE_FACTOR_METRO` | `0.7` | scalar | `low` | Air-conditioned urban underground/elevated rapid transit. In-train filtration reduces particulates, although platform microenvironments remain elevated. |
| `MODE_FACTOR_BUS` | `0.9` | scalar | `low` | Public transit bus travel. Frequent door opening at passenger stops allows heavy roadside diesel exhaust infiltration. |
| `MODE_FACTOR_AUTO_RICKSHAW` | `1.3` | scalar | `low` | Three-wheeled open-cabin paratransit. Cabin breathing zone is directly at tailpipe height ($\approx 0.5\text{--}1.2\,\text{m}$), trapping fresh localized combustion exhaust. |
| `MODE_FACTOR_CAR` | `0.6` | scalar | `low` | Enclosed passenger automobile with closed windows and active air-conditioning cabin recirculating filtration. |
| `MODE_FACTOR_OUTDOOR` | `1.0` | scalar | `high` | Unshielded outdoor atmospheric baseline. |

---

### E. Baseline Adult Breathing Rates by Activity ($\text{m}^3/\text{h}$)

Minute ventilation volumes based on the US EPA *Exposure Factors Handbook* (Chapter 6, Table 6-1) and physiological respiratory literature:

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `BREATHING_RATE_ADULT_SLEEP_M3_H` | `0.30` | $\text{m}^3/\text{h}$ | `high` | Basal nocturnal minute ventilation during slow-wave sleep ($\approx 5.0\,\text{L/min}$). |
| `BREATHING_RATE_ADULT_REST_M3_H` | `0.40` | $\text{m}^3/\text{h}$ | `high` | Sedentary resting state (e.g. reading, watching television, conversational seating). |
| `BREATHING_RATE_ADULT_LIGHT_M3_H` | `0.60` | $\text{m}^3/\text{h}$ | `high` | Light indoor domestic activity (e.g. computer work, household organizing, light study). |
| `BREATHING_RATE_ADULT_WALK_M3_H` | `0.90` | $\text{m}^3/\text{h}$ | `high` | Moderate pedestrian locomotion ($3\text{--}4\,\text{km/h}$). |
| `BREATHING_RATE_ADULT_COOK_M3_H` | `0.70` | $\text{m}^3/\text{h}$ | `high` | Standing domestic kitchen food preparation and culinary tasks. |
| `BREATHING_RATE_ADULT_EXERCISE_M3_H` | `1.80` | $\text{m}^3/\text{h}$ | `high` | Heavy aerobic physical exertion (running, cycling, outdoor sports) with mouth breathing. |

---

### F. Age Group Breathing Multipliers (Dimensionless physiological scale)

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `AGE_BREATHING_MULTIPLIER_TODDLER` | `0.35` | scalar | `high` | Pediatric ventilation volume for toddlers aged 1–3 years ($\approx 35\%$ of adult minute volume, though higher per kg bodyweight). |
| `AGE_BREATHING_MULTIPLIER_CHILD` | `0.55` | scalar | `high` | School-age children aged 4–11 years ($\approx 55\%$ of adult volume). |
| `AGE_BREATHING_MULTIPLIER_TEEN` | `0.85` | scalar | `high` | Adolescents aged 12–17 years approaching adult lung capacity. |
| `AGE_BREATHING_MULTIPLIER_ADULT` | `1.00` | scalar | `high` | Canonical physiological adult reference baseline (ages 18–64). |
| `AGE_BREATHING_MULTIPLIER_SENIOR` | `0.90` | scalar | `high` | Older adults aged 65+ with mildly reduced vital lung volume. |

---

### G. Ventilation & Smog Inversion Thresholds

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `OPEN_WINDOW_MAX_PM25_UG_M3` | `100.0` | $\mu\text{g/m}^3$ | `high` | Upper ceiling for safe natural window airing. If ambient air exceeds $100\,\mu\text{g/m}^3$, opening windows introduces more harm than ventilation benefit. |
| `INVERSION_BLH_M` | `300.0` | meters | `high` | Boundary Layer Height ceiling indicative of a shallow winter temperature inversion that compresses surface emissions into an unvented boundary layer. |
| `STAGNATION_WIND_KMH` | `6.0` | $\text{km/h}$ | `high` | Surface wind speed threshold below which atmospheric dispersion ceases under calm conditions. |
| `STAGNATION_HOURS` | `{20..23, 0..7}` | hour set | `high` | Night-time and early-morning hours where radiative cooling creates atmospheric stability traps. |
| `BASELINE_EXPOSURE_INDEX` | `100.0` | index | `high` | Normalized index reference representing the unmodified baseline daily particulate dose. |

---

### H. Indoor Source Diagnostics & Emission Likelihoods ($0\text{--}1$)

| Constant Name | Value | Confidence | Diagnostic Meaning |
| :--- | :---: | :---: | :--- |
| `INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3` | `60.0` | `high` | Indoor sensor reading above which findings transition from `"suspected"` to `"measured"`. |
| `LIKELIHOOD_BIOMASS_NO_EXHAUST` | `0.95` | `high` | Solid fuel/chulha cooking without mechanical exhaust produces extreme indoor exposure. |
| `LIKELIHOOD_BIOMASS_INTERNAL_EXHAUST` | `0.85` | `high` | Solid biomass cooking with recirculating filter hood that fails to eliminate fine particulates. |
| `LIKELIHOOD_BIOMASS_VENTED_EXHAUST` | `0.60` | `medium` | Solid biomass cooking with ducted chimney; fugitive leakage remains high during loading. |
| `LIKELIHOOD_BIOMASS_DEFAULT` | `0.90` | `high` | Default biomass cooking likelihood when exhaust configuration is unspecified. |
| `LIKELIHOOD_LPG_NO_EXHAUST` | `0.50` | `medium` | Unvented LPG gas stove produces ultrafine particulates and nitrogen dioxide ($NO_2$). |
| `LIKELIHOOD_LPG_INTERNAL_EXHAUST` | `0.35` | `medium` | LPG stove with internal recirculating carbon filter. |
| `LIKELIHOOD_LPG_VENTED_EXHAUST` | `0.15` | `medium` | Ducted exterior exhaust chimney on LPG range effectively extracts culinary aerosols. |
| `LIKELIHOOD_LPG_DEFAULT` | `0.40` | `medium` | Baseline unvented LPG cooking likelihood. |
| `LIKELIHOOD_INCENSE_BURNING` | `0.80` | `high` | Agarbatti and dhoop smoldering emits dense organic aerosols comparable to heavy diesel smoke. |
| `LIKELIHOOD_MOSQUITO_COIL` | `0.85` | `high` | Smoldering mosquito coil in enclosed bedrooms releases PM2.5 equivalent to 75–100 cigarettes. |
| `LIKELIHOOD_TOBACCO_SMOKE` | `0.90` | `high` | Indoor cigarette/bidi smoking creates immediate, dangerous indoor particulate spikes. |
| `LIKELIHOOD_DRY_SWEEPING` | `0.65` | `medium` | Dry broom sweeping mechanically resuspends settled floor dust into the breathing zone. |
| `LIKELIHOOD_PET_DANDER` | `0.30` | `low` | Domestic furred pets contributing coarse organic dander. |
| `LIKELIHOOD_AMBIENT_INFILTRATION` | `0.75` | `medium` | Elevated indoor reading without identified combustion points indicates severe envelope leakage. |

---

### I. Ranking Normalizers, Community Factors & Safety Windows

| Constant Name | Value | Unit | Confidence | Meaning & Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `COST_NORMALIZATION_INR` | `1000.0` | ₹ / month | `high` | Denominator scaling monthly expenditure in the cost-effectiveness ranking formula. |
| `EFFORT_MAX` | `5.0` | scale | `high` | Maximum subjective effort scale (1 = trivial, 5 = major lifestyle modification). |
| `COMMUNITY_AVERAGE_TRIP_KM` | `12.0` | km | `medium` | Average round-trip urban commute distance in Indian metropolitan areas. |
| `COMMUNITY_CO2_KG_PER_KM_CAR` | `0.192` | $\text{kg/km}$ | `high` | Average tailpipe $CO_2$ emission factor for mid-size petrol/diesel passenger automobiles. |
| `COMMUNITY_PM25_QUALITATIVE_NOTE` | *(string)* | - | `high` | Qualitative disclaimer explicitly noting that community pledges reduce traffic emissions but do not represent a calibrated local PM2.5 measurement. |
| `RED_FLAG_OVERRIDE_ACTION` | `"seek medical care now"` | - | `high` | Mandatory clinical directive overriding all environmental and atmospheric planning. |
| `RED_FLAG_NEGATION_WINDOW_CHARS_EN` | `30` | chars | `high` | Backward text scanning window to catch English negation terms (e.g. `"no"`, `"without"`). |
| `RED_FLAG_NEGATION_WINDOW_CHARS_HI` | `25` | chars | `high` | Bidirectional scanning window for Hindi negation particles (e.g. `"नहीं"`, `"बिना"`). |

---

## 2. Open-Meteo Meteorological API Verification

During engineering discovery (Prompt 4 / Prompt 6), Open-Meteo's official API documentation and schemas were investigated. The following facts were confirmed and implemented in [app/data/air_client.py](../app/data/air_client.py):

1. **Hourly $PM_{2.5}$ Variable**:
   - **Endpoint**: `https://air-quality-api.open-meteo.com/v1/air-quality`
   - **Parameter**: `hourly=pm2_5`
   - **Physical Unit**: $\mu\text{g/m}^3$ (micrograms per cubic meter)
   - **Behavior**: Returns hourly predicted particulate concentration for the specified latitude and longitude grid cell.

2. **Hourly Wind Speed Variable**:
   - **Endpoint**: `https://api.open-meteo.com/v1/forecast`
   - **Parameter**: `hourly=wind_speed_10m&wind_speed_unit=kmh`
   - **Physical Unit**: $\text{km/h}$ (kilometers per hour)
   - **Behavior**: Provides 10-meter surface wind velocities used to evaluate atmospheric dispersion.

3. **Boundary Layer Height Availability**:
   - **Endpoint**: `https://api.open-meteo.com/v1/forecast` (Weather Forecast API, *not* the air quality endpoint)
   - **Parameter**: `hourly=boundary_layer_height`
   - **Physical Unit**: Meters ($m$)
   - **Behavior**: Documents the height of the planetary boundary layer. During shallow nocturnal temperature inversions in Delhi winter, this drops to $150\text{--}280\,\text{m}$, trapping emissions near ground level.

4. **Stagnation Proxy Rationale**:
   - When `boundary_layer_height` is null, unmeasured, or when operating in offline/sample fallback mode, nocturnal wind stagnation ($\text{wind} < 6\,\text{km/h}$ between 20:00 and 07:00) serves as a validated diagnostic proxy for thermal trapping.

5. **Coordinate Privacy Truncation**:
   - Geographic coordinates are automatically rounded to 2 decimal places ($\approx 1.1\,\text{km}$) prior to making any external request. This prevents exact residential address exposure while preserving meteorological grid accuracy.
