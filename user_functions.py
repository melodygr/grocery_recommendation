import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import itertools
from datetime import datetime
from statsmodels.graphics.tsaplots import plot_pacf
from matplotlib.pylab import rcParams
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
import statsmodels.api as sm


def visualize_time_series(df, name):
    """Plot time series. Plot annual breakouts for years with all 12 values."""
    df.plot(figsize = (12,4))
    plt.title(name)
    plt.xlabel('Year')
    plt.ylabel('Median House Price')
    plt.savefig('Images/zip_lineplot.png');
    
    # Use pandas grouper to group values using annual frequency
    year_groups = df.groupby(pd.Grouper(freq ='A'))

    # Create a new DataFrame and store yearly values in columns 
    df_annual = pd.DataFrame()

    # print(list(year_groups))
    for yr, group in year_groups:
        if len(group) == 12: # Can only use full years of data
            df_annual[yr.year] = group.values.ravel()
    
    # Plot the yearly groups as subplots
    df_annual.plot(figsize = (13,20), subplots=True, legend=True)
    plt.savefig('Images/annual_breakout.png');

    # Plot overlapping yearly groups 
    df_annual.plot(figsize = (15,10), subplots=False, legend=True)
    plt.savefig('Images/annual_overlap.png');
    
def visualize_all_series(list_of_df, names):
    """Plot a list of time series dataframes together with provided names for legend."""
    df_group = pd.concat(list_of_df, axis=1)
    df_group.columns = names
    df_group.plot(figsize = (12,4), subplots=False, legend=True)
    plt.title('Median House Prices Over Time')
    plt.xlabel('Year')
    plt.ylabel('Median House Price')
    plt.savefig('Images/lineplotallzips.png')
    plt.show();

def stationarity_check(TS):
    """Calculate rolling statistics and plot against original time series, perform and output Dickey Fuller test."""
    # Import adfuller
    from statsmodels.tsa.stattools import adfuller
    
    # Calculate rolling statistics
    roll_mean = TS.rolling(window=24, center=False).mean()
    roll_std = TS.rolling(window=24, center=False).std()
        
    # Perform the Dickey Fuller Test
    dftest = adfuller(TS)
    
    # Plot rolling statistics:
    fig = plt.figure(figsize=(12,6))
    plt.plot(TS, color='blue',label='Original')
    plt.plot(roll_mean.dropna(), color='red', label='Rolling Mean')
    plt.plot(roll_std.dropna(), color='black', label = 'Rolling Std')
    plt.legend(loc='best')
    plt.title('Rolling Mean & Standard Deviation')
    plt.savefig('Images/rolling.png')
    plt.show(block=False)
    
    # Print Dickey-Fuller test results
    print('Results of Dickey-Fuller Test: \n')

    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic', 'p-value', 
                                             '#Lags Used', 'Number of Observations Used'])
    for key,value in dftest[4].items():
        dfoutput['Critical Value (%s)'%key] = value
    print(dfoutput)
    
    return None

def run_arima_models(name, train, test, order, metrics_df, seasonal_order = (0,0,0,0)):
    """Runs baseline ARIMA model and adds metrics and results to a passed dataframe"""
    
    model_metrics = [name, order, seasonal_order]
    
    tic = time.time()
    model = ARIMA(train, order=order, seasonal_order=seasonal_order, freq='MS')
    results = model.fit()
    traintime = time.time() - tic
    
    model_metrics.append(round(traintime, 4))
    
    # Print out summary information on the fit
    # print(results.summary())
    
    model_metrics.extend([round(results.params[0], 2), round(results.params[1], 4), 
                          round(results.params[2], 4), round(results.params[3], 2)])
    model_metrics.append(round(results.aic, 2))
    
    # Get predictions starting from first test index and calculate confidence intervals
    # toc = time.time()
    # pred = results.get_prediction(start = test.index[0], end = test.index[-1], dynamic=True, full_results=True)
    # pred_conf = pred.conf_int()
    # predtime = time.time() - toc
    # model_metrics.append(predtime)
    
    # Add model metrics to passed metrics df    
    series = pd.Series(model_metrics, index = metrics_df.columns)
    metrics_df = metrics_df.append(series, ignore_index=True)
    
    return metrics_df

def grid_search_arima(train, d = 0):
    '''Attempt all pdq parameters to find lowest AIC value'''
    
    # Define the p, d and q parameters to take any value between 0 and 2
    p = q = range(0, 3) #=d

    # Generate all different combinations of p, d, and q triplets
#     pdq = list(itertools.product(p, d, q))
    pq = list(itertools.product(p, q))
    pdq = [(x[0], d, x[1]) for x in pq]          
    
    # Generate all different combinations of seasonal p, d, q and q triplets
    
    ps = ds = qs = range(0, 3)
    psdsqs = list(itertools.product(ps, ds, qs))
    pdqs = [(x[0], x[1], x[2], 12) for x in psdsqs]
    
    # Run a grid with pdq and seasonal pdq parameters calculated above and get the best AIC value
    ans = []
    for comb in pdq:
        for combs in pdqs:
            try:
                grid_model = ARIMA(train, order=comb, seasonal_order=combs, freq='MS')
                grid_results = grid_model.fit()
                ans.append([comb, combs, grid_results.aic])
    #             print('ARIMA {} x {}12 : AIC Calculated ={}'.format(comb, combs, results.aic))
            except:
                continue
    ans_df = pd.DataFrame(ans, columns=['pdq', 'pdqs', 'aic'])
    print(ans_df.loc[ans_df['aic'].idxmin()])
    
    return ans_df

def run_preds_and_plot(model_results, train, test, name, best_diff):
    '''Run predictions, forecasts, plot results, calculate RMSE'''
    
    # Calculate predictions and forecasts
    pred = model_results.get_prediction(start=best_diff[name][0])
    pred_forecast = model_results.get_forecast(steps=pd.to_datetime(test.index[-1]), dynamic=True)
    pred_conf = pred.conf_int()
    pred_forecast_conf = pred_forecast.conf_int()
    
    # Plot observations
    all_data = pd.concat([train, test], axis=0)
    ax = all_data.plot(label='observed', figsize=(12, 6))

    # Plot predictions and forecasts with confidence intervals (unlogged)
    np.exp(pred.predicted_mean).plot(label='Predictions', ax=ax)
    np.exp(pred_forecast.predicted_mean).plot(label='Forecast', ax=ax)
    ax.fill_between(np.exp(pred_conf).index,
                    np.exp(pred_conf).iloc[:, 0],
                    np.exp(pred_conf).iloc[:, 1], color='#F5B14C', alpha=.3)

    # Limit upper end of confidence interval so it doesn't blow up the graph
    bound_conf=[]
    for i in range(len(pred_forecast_conf)):
        if np.exp(pred_forecast_conf).iloc[i,1] > 1.5*np.exp(pred_forecast.predicted_mean)[-1]:
            bound_conf.append(1.5*np.exp(pred_forecast.predicted_mean)[-1])
        else:
            bound_conf.append(np.exp(pred_forecast_conf).iloc[i,1])
    bound_df = pd.DataFrame(bound_conf, index=pred_forecast_conf.index, columns=['upper value'])
    
    ax.fill_between(np.exp(pred_forecast_conf).index,
                    np.exp(pred_forecast_conf).iloc[:, 0],
                    bound_df.iloc[:, 0], color='#F5B14C', alpha=.3)
#                     np.exp(pred_forecast_conf).iloc[:, 1], color='g', alpha=.3)
    ax.fill_betweenx(ax.get_ylim(), test.index[0], test.index[-1], alpha=.1, zorder=-1)
    ax.set_xlabel('Date')
    ax.set_ylabel('Median House Prices')
    plt.legend()
    imagename=str("Images/"+name+"pred.png")
    plt.savefig(imagename)
    plt.show()
    
    # Compute the train mean squared error
    rmse_train = np.sqrt(((np.exp(pred.predicted_mean) - train.value[best_diff[name][0]:]) ** 2).mean())
    print('The Root Mean Squared Error of {} predictions is {}'.format(name, round(rmse_train, 2)))

    # Compute the test mean squared error
    rmse_test = np.sqrt(((np.exp(pred_forecast.predicted_mean) - test.value) ** 2).mean())
    print('The Root Mean Squared Error of {} forecasts is {}'.format(name, round(rmse_test, 2)))
    
    # Plot 2 years
    ax = all_data.plot(label='observed', figsize=(12, 6))
    np.exp(pred.predicted_mean).plot(label='Predictions', ax=ax)
    np.exp(pred_forecast.predicted_mean).plot(label='Forecast', ax=ax)
    ax.fill_between(np.exp(pred_conf).index,
                    np.exp(pred_conf).iloc[:, 0],
                    np.exp(pred_conf).iloc[:, 1], color='#F5B14C', alpha=.3)
    ax.fill_between(np.exp(pred_forecast_conf).index,
                    np.exp(pred_forecast_conf).iloc[:, 0],
                    bound_df.iloc[:, 0], color='#F5B14C', alpha=.3)
    ax.fill_betweenx(ax.get_ylim(), test.index[0], test.index[-1], alpha=.1, zorder=-1)
    ax.set_xlabel('Date')
    ax.set_ylabel('Median House Prices')
    ax.set_xlim(xmin=train.index[-12])
    plt.legend()
    imagename=str("Images/2yr"+name+"pred.png")
    plt.savefig(imagename)
    plt.show()
    
    return pred, pred_forecast, rmse_train, rmse_test

def track_final_metrics(grid_search, results, name):
    '''Add model parameters and results to a dictionary and return'''
    
    metrics = {'name':name, 'order':grid_search['pdq'].loc[grid_search['aic'].idxmin()],
                'seasonal order':grid_search['pdqs'].loc[grid_search['aic'].idxmin()]}
    for i in range(len(results.params)):
        metrics.update({results.params.index[i]:round(results.params[i], 4)})

    metrics.update({'aic':round(results.aic, 2)})
               
    return metrics