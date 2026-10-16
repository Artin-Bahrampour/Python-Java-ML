# Model Card: Solar PV Generation Forecasting

## Intended use

Demonstrate a reproducible short-horizon regression workflow for hourly PV energy generation. The project is educational and suitable for portfolio review, experimentation, and engineering interviews.

## Model output

The model estimates `pv_generation_kwh`, the energy generated during a one-hour interval. It is a point forecast and does not provide a prediction interval.

## Training data

Data is generated deterministically by `pv_forecast.data.generate_dataset`. The generator uses synthetic solar geometry, weather-like covariates, and a simplified PV response. No real customer, personal, or operational data is included.

## Features

- Cyclical hour and annual-season encodings.
- Clear-sky irradiance proxy.
- Synthetic cloud-cover, temperature, and humidity forecasts.
- Generation lags from 24 and 168 hours before the target interval.

## Evaluation

The earliest 70% of rows are used for fitting, the next 15% for validation-based model selection, and the final 15% for a single held-out test evaluation. The seasonal-naive baseline is evaluated alongside the selected model. Metrics include MAE, RMSE, and R².

## Known limitations and risks

- Synthetic-to-real domain shift is substantial and unquantified.
- Forecast-vintage alignment is assumed rather than simulated from a real weather provider.
- A rolling one-hour-ahead setup assumes prior generation observations are available.
- R² can be difficult to interpret for strongly seasonal or near-zero nighttime targets.
- PSI is a heuristic drift indicator and can react to benign seasonal changes.

## Use restrictions

Do not use this model for grid dispatch, trading, safety-critical decisions, or commercial commitments without real-data validation, operational review, uncertainty quantification, and monitoring.
