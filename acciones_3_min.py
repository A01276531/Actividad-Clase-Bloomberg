# -*- coding: utf-8 -*-
"""Acciones 3 min

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1u91oLanU2UJesaNb6KrYbGDZMbT2bS_P
"""

import pandas as pd
import numpy as np
from google.colab import files
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Upload Excel files
print("Please upload the Excel files: AAPL 3min.xlsx, NVDA 3min.xlsx, GOOGL 3min.xlsx")
uploaded = files.upload()

# File names (adjust for Colab's renaming, e.g., 'AAPL 3min (10).xlsx')
file_names = {
    'AAPL': next((f for f in uploaded.keys() if 'AAPL 3min' in f), None),
    'NVDA': next((f for f in uploaded.keys() if 'NVDA 3min' in f), None),
    'GOOGL': next((f for f in uploaded.keys() if 'GOOGL 3min' in f), None)
}

# Read Excel files
aapl = pd.read_excel(file_names['AAPL'])
nvda = pd.read_excel(file_names['NVDA'])
googl = pd.read_excel(file_names['GOOGL'])

# Specify the closing price column name
close_column = 'CLOSE'

# Extract closing price columns
try:
    aapl_close = aapl[close_column]
    nvda_close = nvda[close_column]
    googl_close = googl[close_column]
except KeyError:
    raise KeyError(f"Column '{close_column}' not found in one or more Excel files. Please verify the column name.")

# Check for NaN or inf values
def check_invalid_values(series, name):
    nan_count = series.isna().sum()
    inf_count = np.isinf(series).sum()
    print(f"\nChecking {name} for invalid values:")
    print(f"NaN count: {nan_count}")
    print(f"Inf count: {inf_count}")
    return nan_count > 0 or inf_count > 0

# Perform checks
aapl_invalid = check_invalid_values(aapl_close, 'AAPL')
nvda_invalid = check_invalid_values(nvda_close, 'NVDA')
googl_invalid = check_invalid_values(googl_close, 'GOOGL')

# Clean data by dropping rows with NaN or inf
if aapl_invalid or nvda_invalid or googl_invalid:
    print("\nCleaning data by dropping rows with NaN or inf values...")
    aapl_close = aapl_close.replace([np.inf, -np.inf], np.nan).dropna()
    nvda_close = nvda_close.replace([np.inf, -np.inf], np.nan).dropna()
    googl_close = googl_close.replace([np.inf, -np.inf], np.nan).dropna()
    print(f"Remaining lengths: AAPL={len(aapl_close)}, NVDA={len(nvda_close)}, GOOGL={len(googl_close)}")
else:
    print(f"\nSeries lengths: AAPL={len(aapl_close)}, NVDA={len(nvda_close)}, GOOGL={len(googl_close)}")

# Verify no invalid values remain
if aapl_close.isna().sum() > 0 or np.isinf(aapl_close).sum() > 0:
    raise ValueError("AAPL data still contains NaN or inf values after cleaning.")
if nvda_close.isna().sum() > 0 or np.isinf(nvda_close).sum() > 0:
    raise ValueError("NVDA data still contains NaN or inf values after cleaning.")
if googl_close.isna().sum() > 0 or np.isinf(googl_close).sum() > 0:
    raise ValueError("GOOGL data still contains NaN or inf values after cleaning.")

# Function for ADF unit root test
def adf_test(series, name):
    result = adfuller(series, autolag='AIC')
    print(f'\nADF Test for {name}:')
    print(f'ADF Statistic: {result[0]:.4f}')
    print(f'p-value: {result[1]:.4f}')
    print('Stationary' if result[1] < 0.05 else 'Non-Stationary')
    return result[1] < 0.05

# Perform ADF tests
print("\n=== Unit Root Test Interpretation ===")
print("The ADF test checks if the series is stationary (no unit root).")
print("A p-value < 0.05 indicates stationarity, meaning no differencing is needed.")
aapl_stationary = adf_test(aapl_close, 'AAPL')
nvda_stationary = adf_test(nvda_close, 'NVDA')
googl_stationary = adf_test(googl_close, 'GOOGL')

# Determine differencing order for ARIMA
aapl_d = 0 if aapl_stationary else 1
nvda_d = 0 if nvda_stationary else 1
googl_d = 0 if googl_stationary else 1
# Note: If GOOGL differenced series is non-stationary, set googl_d = 2:
# googl_d = 2
# googl_diff = googl_close.diff().diff().dropna()

# If non-stationary, difference the series
aapl_diff = aapl_close if aapl_stationary else aapl_close.diff().dropna()
nvda_diff = nvda_close if nvda_stationary else nvda_close.diff().dropna()
googl_diff = googl_close if googl_stationary else googl_close.diff().dropna()

# Print lengths of differenced series
print(f"\nDifferenced series lengths: AAPL={len(aapl_diff)}, NVDA={len(nvda_diff)}, GOOGL={len(googl_diff)}")

# Verify stationarity of differenced series
print("\nVerifying stationarity of differenced series (if applicable):")
adf_test(aapl_diff, 'AAPL Differenced')
adf_test(nvda_diff, 'NVDA Differenced')
adf_test(googl_diff, 'GOOGL Differenced')

# Plot ACF and PACF
def plot_correlograms(series, name, max_lags=20):
    n_obs = len(series)
    nlags = min(max_lags, n_obs // 2 - 1) if n_obs >= 4 else 1
    if nlags < 1:
        print(f"Skipping correlogram for {name}: too few observations ({n_obs}).")
        return
    print(f"Generating correlogram for {name} with {nlags} lags.")
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plot_acf(series, lags=nlags, ax=plt.gca())
    plt.title(f'ACF for {name}')
    plt.subplot(1, 2, 2)
    plot_pacf(series, lags=nlags, ax=plt.gca())
    plt.title(f'PACF for {name}')
    plt.tight_layout()
    plt.savefig(f'{name}_correlogram.png')
    plt.show()  # Display inline
    plt.close()

# Generate correlograms
print("\n=== Correlogram Interpretation ===")
print("ACF shows autocorrelation at different lags; PACF shows partial autocorrelation.")
print("Significant spikes at lag k suggest AR(k) or MA(k) terms for ARIMA.")
print("Here, ARIMA(1,d,1) is used, but correlograms may suggest other orders.")
plot_correlograms(aapl_diff, 'AAPL')
plot_correlograms(nvda_diff, 'NVDA')
plot_correlograms(googl_diff, 'GOOGL')
print("\nCorrelograms saved as 'AAPL_correlogram.png', 'NVDA_correlogram.png', 'GOOGL_correlogram.png' (if generated).")

# Fit ARIMA models
def fit_arima(series, name, d):
    if len(series) < 5:
        print(f"Skipping ARIMA for {name}: too few observations ({len(series)}).")
        return None
    order = (1, d, 1)  # ARIMA(1,d,1)
    try:
        model = ARIMA(series, order=order).fit()
        print(f'\nARIMA(1,{d},1) Model Summary for {name}:')
        print(model.summary())
        return model
    except Exception as e:
        print(f"ARIMA fitting failed for {name}: {str(e)}")
        return None

# Fit ARIMA models
print("\n=== ARIMA Model Interpretation ===")
print("ARIMA(p,d,q) models forecast time series. Here, p=1 (AR), q=1 (MA), d=0 or 1.")
print("Check coefficients' p-values (< 0.05 for significance) and AIC (lower is better).")
aapl_arima = fit_arima(aapl_close, 'AAPL', aapl_d)
nvda_arima = fit_arima(nvda_close, 'NVDA', nvda_d)
googl_arima = fit_arima(googl_close, 'GOOGL', googl_d)

# Cointegration tests
def coint_test(series1, series2, name1, name2):
    if len(series1) < 5 or len(series2) < 5:
        print(f"Skipping cointegration test for {name1}-{name2}: too few observations.")
        return False
    try:
        score, p_value, _ = coint(series1, series2)
        print(f'\nCointegration Test between {name1} and {name2}:')
        print(f'Test Statistic: {score:.4f}')
        print(f'p-value: {p_value:.4f}')
        print('Cointegrated' if p_value < 0.05 else 'Not Cointegrated')
        return p_value < 0.05
    except Exception as e:
        print(f"Cointegration test failed for {name1}-{name2}: {str(e)}")
        return False

# Perform cointegration tests
print("\n=== Cointegration Test Interpretation ===")
print("Cointegration tests check if two series have a stable long-run relationship.")
print("A p-value < 0.05 suggests cointegration (series move together over time).")
coint_aapl_nvda = coint_test(aapl_close, nvda_close, 'AAPL', 'NVDA')
coint_aapl_googl = coint_test(aapl_close, googl_close, 'AAPL', 'GOOGL')
coint_nvda_googl = coint_test(nvda_close, googl_close, 'NVDA', 'GOOGL')

# Forecasting and plotting
def forecast_and_plot(model, series, name, steps=1):
    if model is None:
        print(f"Skipping forecast for {name}: no valid ARIMA model.")
        return
    if len(series) < 5:
        print(f"Skipping forecast for {name}: too few observations ({len(series)}).")
        return
    try:
        forecast = model.get_forecast(steps=steps)
        forecast_mean = forecast.predicted_mean
        conf_int = forecast.conf_int()

       # Plot actual vs forecast
        plt.figure(figsize=(10, 6))
        n_actual = min(50, len(series))
        plt.plot(series[-n_actual:], label='Actual', color='blue')
        forecast_index = range(len(series), len(series) + steps)
        plt.plot(forecast_index, forecast_mean, label='Forecast', color='red')
        plt.fill_between(forecast_index, conf_int.iloc[:, 0], conf_int.iloc[:, 1],
                         color='pink', alpha=0.3, label='95% Confidence Interval')
        plt.title(f'{name} Closing Price Forecast (1 Minute Ahead)')
        plt.xlabel('Time (Minute)')
        plt.ylabel('Closing Price')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'{name}_forecast.png')
        plt.show()  # Display inline
        plt.close()
        print(f"Forecast plot generated and saved for {name} as '{name}_forecast.png'.")
    except Exception as e:
        print(f"Forecasting failed for {name}: {str(e)}")

# Generate forecasts and plots
print("\n=== Forecast Interpretation ===")
print("Forecasts predict the next 1 minute of closing prices based on 3-minute data.")
print("Red point shows the forecast, error bar shows the 95% confidence interval.")
print("Narrow intervals suggest higher confidence in the forecast.")
forecast_and_plot(aapl_arima, aapl_close, 'AAPL')
forecast_and_plot(nvda_arima, nvda_close, 'NVDA')
forecast_and_plot(googl_arima, googl_close, 'GOOGL')
print("\nForecast plots saved as 'AAPL_forecast.png', 'NVDA_forecast.png', 'GOOGL_forecast.png' (if generated).")

import pandas as pd
import numpy as np
from google.colab import files
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Upload Excel files
print("Please upload the Excel files: AAPL 3min.xlsx, NVDA 3min.xlsx, GOOGL 3min.xlsx")
uploaded = files.upload()

# File names (adjust for Colab's renaming, e.g., 'AAPL 3min (10).xlsx')
file_names = {
    'AAPL': next((f for f in uploaded.keys() if 'AAPL 3min' in f), None),
    'NVDA': next((f for f in uploaded.keys() if 'NVDA 3min' in f), None),
    'GOOGL': next((f for f in uploaded.keys() if 'GOOGL 3min' in f), None)
}

# Read Excel files
aapl = pd.read_excel(file_names['AAPL'])
nvda = pd.read_excel(file_names['NVDA'])
googl = pd.read_excel(file_names['GOOGL'])

# Specify the closing price column name
close_column = 'CLOSE'

# Extract closing price columns
try:
    aapl_close = aapl[close_column]
    nvda_close = nvda[close_column]
    googl_close = googl[close_column]
except KeyError:
    raise KeyError(f"Column '{close_column}' not found in one or more Excel files. Please verify the column name.")

# Check for NaN or inf values
def check_invalid_values(series, name):
    nan_count = series.isna().sum()
    inf_count = np.isinf(series).sum()
    print(f"\nChecking {name} for invalid values:")
    print(f"NaN count: {nan_count}")
    print(f"Inf count: {inf_count}")
    return nan_count > 0 or inf_count > 0

# Perform checks
aapl_invalid = check_invalid_values(aapl_close, 'AAPL')
nvda_invalid = check_invalid_values(nvda_close, 'NVDA')
googl_invalid = check_invalid_values(googl_close, 'GOOGL')

# Clean data by dropping rows with NaN or inf
if aapl_invalid or nvda_invalid or googl_invalid:
    print("\nCleaning data by dropping rows with NaN or inf values...")
    aapl_close = aapl_close.replace([np.inf, -np.inf], np.nan).dropna()
    nvda_close = nvda_close.replace([np.inf, -np.inf], np.nan).dropna()
    googl_close = googl_close.replace([np.inf, -np.inf], np.nan).dropna()
    print(f"Remaining lengths: AAPL={len(aapl_close)}, NVDA={len(nvda_close)}, GOOGL={len(googl_close)}")
else:
    print(f"\nSeries lengths: AAPL={len(aapl_close)}, NVDA={len(nvda_close)}, GOOGL={len(googl_close)}")

# Verify no invalid values remain
if aapl_close.isna().sum() > 0 or np.isinf(aapl_close).sum() > 0:
    raise ValueError("AAPL data still contains NaN or inf values after cleaning.")
if nvda_close.isna().sum() > 0 or np.isinf(nvda_close).sum() > 0:
    raise ValueError("NVDA data still contains NaN or inf values after cleaning.")
if googl_close.isna().sum() > 0 or np.isinf(googl_close).sum() > 0:
    raise ValueError("GOOGL data still contains NaN or inf values after cleaning.")

# Function for ADF unit root test
def adf_test(series, name):
    result = adfuller(series, autolag='AIC')
    print(f'\nADF Test for {name}:')
    print(f'ADF Statistic: {result[0]:.4f}')
    print(f'p-value: {result[1]:.4f}')
    print('Stationary' if result[1] < 0.05 else 'Non-Stationary')
    return result[1] < 0.05

# Perform ADF tests
print("\n=== Unit Root Test Interpretation ===")
print("The ADF test checks if the series is stationary (no unit root).")
print("A p-value < 0.05 indicates stationarity, meaning no differencing is needed.")
aapl_stationary = adf_test(aapl_close, 'AAPL')
nvda_stationary = adf_test(nvda_close, 'NVDA')
googl_stationary = adf_test(googl_close, 'GOOGL')

# Determine differencing order for ARIMA
aapl_d = 0 if aapl_stationary else 1
nvda_d = 0 if nvda_stationary else 1
googl_d = 0 if googl_stationary else 1
# Note: GOOGL differenced series is non-stationary (p=0.1301). Set googl_d = 2 if needed:
# googl_d = 2
# googl_diff = googl_close.diff().diff().dropna()

# If non-stationary, difference the series
aapl_diff = aapl_close if aapl_stationary else aapl_close.diff().dropna()
nvda_diff = nvda_close if nvda_stationary else nvda_close.diff().dropna()
googl_diff = googl_close if googl_stationary else googl_close.diff().dropna()

# Print lengths of differenced series
print(f"\nDifferenced series lengths: AAPL={len(aapl_diff)}, NVDA={len(nvda_diff)}, GOOGL={len(googl_diff)}")

# Verify stationarity of differenced series
print("\nVerifying stationarity of differenced series (if applicable):")
adf_test(aapl_diff, 'AAPL Differenced')
adf_test(nvda_diff, 'NVDA Differenced')
adf_test(googl_diff, 'GOOGL Differenced')

# Plot ACF and PACF
def plot_correlograms(series, name, max_lags=20):
    n_obs = len(series)
    nlags = min(max_lags, n_obs // 2 - 1) if n_obs >= 4 else 1
    if nlags < 1:
        print(f"Skipping correlogram for {name}: too few observations ({n_obs}).")
        return
    print(f"Generating correlogram for {name} with {nlags} lags.")
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plot_acf(series, lags=nlags, ax=plt.gca())
    plt.title(f'ACF for {name}')
    plt.subplot(1, 2, 2)
    plot_pacf(series, lags=nlags, ax=plt.gca())
    plt.title(f'PACF for {name}')
    plt.tight_layout()
    plt.savefig(f'{name}_correlogram.png')
    plt.show()  # Display inline
    plt.close()

# Generate correlograms
print("\n=== Correlogram Interpretation ===")
print("ACF shows autocorrelation at different lags; PACF shows partial autocorrelation.")
print("Significant spikes at lag k suggest AR(k) or MA(k) terms for ARIMA.")
print("Here, ARIMA(1,d,1) is used, but correlograms may suggest other orders.")
plot_correlograms(aapl_diff, 'AAPL')
plot_correlograms(nvda_diff, 'NVDA')
plot_correlograms(googl_diff, 'GOOGL')
print("\nCorrelograms saved as 'AAPL_correlogram.png', 'NVDA_correlogram.png', 'GOOGL_correlogram.png' (if generated).")

# Fit ARIMA models
def fit_arima(series, name, d):
    if len(series) < 5:
        print(f"Skipping ARIMA for {name}: too few observations ({len(series)}).")
        return None
    order = (1, d, 1)  # ARIMA(1,d,1)
    try:
        model = ARIMA(series, order=order).fit()
        print(f'\nARIMA(1,{d},1) Model Summary for {name}:')
        print(model.summary())
        return model
    except Exception as e:
        print(f"ARIMA fitting failed for {name}: {str(e)}")
        return None

# Fit ARIMA models
print("\n=== ARIMA Model Interpretation ===")
print("ARIMA(p,d,q) models forecast time series. Here, p=1 (AR), q=1 (MA), d=0 or 1.")
print("Check coefficients' p-values (< 0.05 for significance) and AIC (lower is better).")
aapl_arima = fit_arima(aapl_close, 'AAPL', aapl_d)
nvda_arima = fit_arima(nvda_close, 'NVDA', nvda_d)
googl_arima = fit_arima(googl_close, 'GOOGL', googl_d)

# Cointegration tests
def coint_test(series1, series2, name1, name2):
    if len(series1) < 5 or len(series2) < 5:
        print(f"Skipping cointegration test for {name1}-{name2}: too few observations.")
        return False
    try:
        score, p_value, _ = coint(series1, series2)
        print(f'\nCointegration Test between {name1} and {name2}:')
        print(f'Test Statistic: {score:.4f}')
        print(f'p-value: {p_value:.4f}')
        print('Cointegrated' if p_value < 0.05 else 'Not Cointegrated')
        return p_value < 0.05
    except Exception as e:
        print(f"Cointegration test failed for {name1}-{name2}: {str(e)}")
        return False

# Perform cointegration tests
print("\n=== Cointegration Test Interpretation ===")
print("Cointegration tests check if two series have a stable long-run relationship.")
print("A p-value < 0.05 suggests cointegration (series move together over time).")
coint_aapl_nvda = coint_test(aapl_close, nvda_close, 'AAPL', 'NVDA')
coint_aapl_googl = coint_test(aapl_close, googl_close, 'AAPL', 'GOOGL')
coint_nvda_googl = coint_test(nvda_close, googl_close, 'NVDA', 'GOOGL')

# Forecasting and plotting
def forecast_and_plot(model, series, name, steps=10):
    if model is None:
        print(f"Skipping forecast for {name}: no valid ARIMA model.")
        return
    if len(series) < 5:
        print(f"Skipping forecast for {name}: too few observations ({len(series)}).")
        return
    try:
        forecast = model.get_forecast(steps=steps)
        forecast_mean = forecast.predicted_mean
        conf_int = forecast.conf_int()

        # Plot actual vs forecast
        plt.figure(figsize=(10, 6))
        n_actual = min(50, len(series))
        plt.plot(series[-n_actual:], label='Actual', color='blue')
        forecast_index = range(len(series), len(series) + steps)
        plt.plot(forecast_index, forecast_mean, label='Forecast', color='red')
        plt.fill_between(forecast_index, conf_int.iloc[:, 0], conf_int.iloc[:, 1],
                         color='pink', alpha=0.3, label='95% Confidence Interval')
        plt.title(f'{name} Closing Price Forecast (3 Minutes Ahead)')
        plt.xlabel('Time (Minutes)')
        plt.ylabel('Closing Price')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'{name}_forecast.png')
        plt.show()  # Display inline
        plt.close()
        print(f"Forecast plot generated and saved for {name} as '{name}_forecast.png'.")
    except Exception as e:
        print(f"Forecasting failed for {name}: {str(e)}")

# Generate forecasts and plots
print("\n=== Forecast Interpretation ===")
print("Forecasts predict the next 1 minute of closing prices.")
print("Red line shows the forecast, pink area shows the 95% confidence interval.")
print("Narrow intervals suggest higher confidence in the forecast.")
forecast_and_plot(aapl_arima, aapl_close, 'AAPL')
forecast_and_plot(nvda_arima, nvda_close, 'NVDA')
forecast_and_plot(googl_arima, googl_close, 'GOOGL')
print("\nForecast plots saved as 'AAPL_forecast.png', 'NVDA_forecast.png', 'GOOGL_forecast.png' (if generated).")