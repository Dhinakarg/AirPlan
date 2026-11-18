# Evaluation Methodology & Metrics

This document outlines the evaluation framework for AirLedger's clean-air recommendations, mathematical model accuracy, and community intervention impact.

## 1. Physical Accuracy Metrics
- **Mean Absolute Error (MAE)** against calibrated reference indoor monitor data.
- **Root Mean Square Error (RMSE)** for single-zone mass balance transient response during cooking and filtration events.
- **Physical Monotonicity Invariants**: Verification via property-based testing (Hypothesis) that filtration always reduces or maintains particulate concentration.

## 2. Health & Vulnerability Metrics
- **Time-Weighted Daily Average Inhaled Dose**: Exposure calculation across heterogeneous activity schedules.
- **WHO & NAAQS Threshold Exceedance Hours**: Tracking hours above 15 $\mu\text{g/m}^3$ (WHO) and 60 $\mu\text{g/m}^3$ (Indian standard).
- **Vulnerability-Adjusted Risk Multiplier**: Individualized physiological sensitivity weightings for infants, elderly, and respiratory patients.

## 3. Intervention Cost-Effectiveness
- **$\Delta\text{PM}_{2.5} / \text{Cost}$ Ratio**: Micrograms per cubic meter reduction per 100 INR spent on low-cost mitigations (e.g. Corsi-Rosenthal boxes, weatherstripping, N95 masks).

