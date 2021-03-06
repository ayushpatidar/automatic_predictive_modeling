import sys
import itertools
import warnings
from math import sqrt

import numpy as np
from pyramid.arima import auto_arima
from sklearn.metrics import mean_squared_error
from stationary.stationary_test import test_stationary
from statsmodels.tsa.api import ARIMA
from statsmodels.tsa.api import ExponentialSmoothing
from statsmodels.tsa.api import Holt
from statsmodels.tsa.api import SimpleExpSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import acf
from statsmodels.tsa.stattools import pacf

sys.path.append('/home/ayushpatidar/PycharmProjects/Automatic_predictive_modeling')
from mysqlclient import connection

warnings.filterwarnings("ignore")


def get_params_p(df):
    pa = pacf(df)
    lis = list()
    for i in range(len(pa)):
        if pa[i] > 0.5:
            lis.append(i)
        if pa[i] > -0.5 and pa[i] < 0:
            lis.append(i)

    return lis


def get_params_q(df):
    ac = acf(df)
    lis = list()

    for i in range(len(ac)):
        if ac[i] > 0.5:
            lis.append(i)
        if ac[i] > -0.5 and ac[i] < 0:
            lis.append(i)

    return lis


def insert_into_database(model_name, model_acc, model_error):

    print(model_name, model_acc)
    print("in database")
    """THIS FUNCTION IS USED FOR ADDING THE TIME SERIES FOR-
          -ECAST RESULTS INTO THE DATABASE"""

    db = connection()
    cur = db.cursor()

    sql = """INSERT INTO RESULTS (MODEL_NAME, MODEL_ACCURACY, TRAINING_ERROR)
            VALUES(%s, %s, %s)"""

    try:
        print(model_error, model_name, model_acc)
        data = (model_name, model_acc, model_error)
        cur.execute(sql,data)
        print("time series results addded in DB")
        db.commit()
        db.close()


    except Exception as e:
        db.rollback()
        db.close()
        print("error while adding results in time_series db,{}".format(e))


def log_transformation(df):


    Y = df.columns.values
    print((df[Y].dtypes))
    print((df.dtypes))

    # MAKE LOG TRASFORMATION
    is_log_transform = False
    """
    the lis will keep track of the indexes which are negative 
    and we have added an constant to make it positive
    
    """
    lis = list()

    try:
        lis = df[Y].values
        min1 = min(lis)

        if min1 <= 0:
            for i in df.index:
                if df[i][Y] < 0:
                    lis.append(i)
                    df[i][Y] = df[i][Y] + abs(min1)

        df = np.log(df[Y])
        is_log_transform = True


    except Exception as e:
        print(("error in making log transform {}", e))

    return (is_log_transform, df)


def train_test_split(df):
    # FUNCTION FOR RETURNING TRAIN AND TEST HOLDOUT SETS 85 PERCENT  IS USED FOR TRAINING AND 15 PERCENT IS USED FOR TESTING
    split = int(df.shape[0] * (0.65))
    train = df[0:split]
    test = df[split:]

    return (train, test)


def TIME_SERIES_ALGO(df, bool_stat):
    dict_rmse = dict()

    bool_log, df_log = log_transformation(df)
    col = df.columns[0]
    # 1.. NAIVE APPROACH
    # IN THIS APPROCAH WE ASSIGN RECENT VALUE TO THE TEST DATAFRAME

    try:
        train, test = train_test_split(df)

        y_prd = np.asarray([train.ix[train.shape[0] - 1].values[0]] * (test.shape[0]))

        rs_naive = sqrt(mean_squared_error(test[col].values, y_prd))
        print(rs_naive)
        dict_rmse["naive"] = rs_naive
        insert_into_database("NAIVE", rs_naive, "{}")

        if bool_log:
            # PERFORM SAME ABOVE THING FOR LOG TRANSFORMED DATA
            train, test = train_test_split(df_log)

            y_prd = np.asarray([train.ix[train.shape[0] - 1].values[0]] * (test.shape[0]))

            y_prd = np.exp(y_prd)

            rs_naive_log = sqrt(mean_squared_error(test[col].values, y_prd))
            print(rs_naive_log)
            dict_rmse["naive_log"] = rs_naive_log
            insert_into_database("NAIVE", rs_naive_log, "{}")

    except Exception as e:
        insert_into_database("NAIVE",None , e)
        print(("error in modelling in naive approach,{}".format(e)))

    # 2..SIMPLE AVERAGE
    try:

        train, test = train_test_split(df)
        mean_forecast = train[col].mean()
        y_prd = np.asarray([mean_forecast] * test.shape[0])
        rs_mean = sqrt(mean_squared_error(test[col].values, y_prd))
        dict_rmse["simple_avg"] = rs_mean
        insert_into_database("SIMPLE_AVG", rs_mean, "{}")

        if bool_log:
            train, test = train_test_split(df_log)
            mean_forecast = train[col].mean()
            y_prd = np.asarray([mean_forecast] * test.shape[0])

            y_prd = np.exp(y_prd)

            rs_mean = sqrt(mean_squared_error(test[col].values, y_prd))
            dict_rmse["simple_avg_log"] = rs_mean
            insert_into_database("SIMPLE_AVG", rs_mean, "{}")

    except Exception as e:
        insert_into_database("SIMPLE_AVG", None, e)
        print(("error in moving average,{}".format(e)))

    # 3..MOVING AVERAGE

    # IN PROGRESS HAVE TO MODIFY IT...
    try:
        train, test = train_test_split(df)
        for i in range(25, 90):
            # As rolling mean returns mean fo ecah row we want mean f only last row because it is onlu used to forecast
            mean_moving = train[col].rolling(i).mean().ix[train.shape[0] - 1]
            print(mean_moving)
            y_prd = np.asarray([mean_moving] * test.shape[0])
            rs_moving = sqrt(mean_squared_error(test[col].values, y_prd))
            insert_into_database("MVG_AVG", rs_moving, "{}")

    except Exception as e:
        insert_into_database("MVG_AVG", None, e)
        print(("error in moving average,{}".format(e)))
    try:

        if bool_log:
            for i in range(25, 90):
                train, test = train_test_split(df_log)

                # print(type(train[col].rolling(i).mean()))
                mean_moving = train[col].rolling(i).mean().ix[train.shape[0] - 1]

                y_prd = np.array([mean_moving] * test.shape[0])
                print(y_prd)
                y_prd = np.exp(y_prd)

                rs_moving_log = sqrt(mean_squared_error(test[col].values, y_prd))
                insert_into_database("MVG_AVERAGE", rs_moving_log, "{}")


    except Exception as e:
        insert_into_database("MVG_AVERAGE", None, e)
        print(("error in log moving average model, {}".format(e)))

    # 4.. SIMPLE EXPONENTIAL SMOOTHING
    try:
        train, test = train_test_split(df)
        fit2 = SimpleExpSmoothing(df[col]).fit(smoothing_level=0.6, optimized=False)
        # print(test.index[0])
        # print(test.index[test.shape[0]-1])
        y_prd = fit2.forecast(len(test))
        print(y_prd)

        rs_simple = sqrt(mean_squared_error(test.values, y_prd))
        dict_rmse["simple"] = rs_simple
        insert_into_database("SIMPLE_EXP", rs_simple, "{}")


    except Exception as e:
        print(("error is simple exp without log,{}".format(e)))
        insert_into_database("SIMPLE_EXP", None, e)

    try:
        if bool_log:
            train, test = train_test_split(df_log)
            fit2 = SimpleExpSmoothing(df[col]).fit(smoothing_level=0.6, optimized=False)
            y_prd = fit2.forecast(len(test))
            y_prd = np.exp(y_prd)
            rs_simple = sqrt(mean_squared_error(test.values, y_prd))
            dict_rmse["simple_log"] = rs_simple
            insert_into_database("SIMPLE_EXP", rs_simple, "{}")

    except Exception as e:
        insert_into_database("SIMPLE_EXP", None, e)
        print(("simple exponential smoothing log,{}".format(e)))



    # HOT LINEAR METHOD FOR FORECASTING
    try:
        train, test = train_test_split(df)
        fit2 = Holt(train[col], exponential=True, damped=False).fit()
        y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
        rs_hotl = sqrt(mean_squared_error(test[col].values, y_prd))
        dict_rmse["rs_hotl"] = rs_hotl
        insert_into_database("HOLT_LINEAR", rs_hotl, "{}")

        if bool_log:
            train, test = train_test_split(df)
            fit2 = Holt(train[col], exponential=True, damped=False).fit()
            y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
            y_prd = np.exp(y_prd)
            rs_hotl_log = sqrt(mean_squared_error(test[col].values, y_prd))
            dict_rmse["rs_hotl_log"] = rs_hotl_log
            insert_into_database("HOLT_LINEAR", rs_hotl_log, "{}")


    except Exception as e:
        insert_into_database("HOLT_LINEAR", None, e)
        print(("error in HOLT linear forecasting in without damped.{}".format(e)))

    try:

        fit2 = Holt(train[col], exponential=True, damped=True).fit()
        y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
        rs_holtld = sqrt(mean_squared_error(test[col].values, y_prd))
        dict_rmse["rs_holtld"] = rs_holtld
        insert_into_database("HOLT_LINEAR", rs_holtld, "{}")

        if bool_log:
            fit2 = Holt(train[col], exponential=True, damped=True).fit()
            y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
            y_prd = np.exp(y_prd)
            rs_holtld = sqrt(mean_squared_error(test[col].values, y_prd))
            dict_rmse["rs_holtld"] = rs_holtld
            insert_into_database("HOLT_LINEAR", rs_holtld, "{}")

    except Exception as e:
        print(("error in HOLT linear smoothing  damped,{}".format(e)))
        insert_into_database("HOLT_LINEAR", None, e)



    # HOLT WINTERS FORECASTING..
    try:
        train, test = train_test_split(df)
        # print("fmmf")
        fit2 = ExponentialSmoothing(test[col], trend="mul", seasonal="mul", seasonal_periods=12).fit()
        y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
        rs_hlw = sqrt(mean_squared_error(test[col].values, y_prd))
        print(rs_hlw)
        dict_rmse["rs_hlw"] = rs_hlw
        insert_into_database("HOLT_WINTER", rs_hlw, "{}")

        if bool_log:
            train, test = train_test_split(df_log)
            fit2 = ExponentialSmoothing(test[col], trend="add", seasonal="add",
                                        seasonal_periods=12).fit()
            y_prd = fit2.predict(test.index.values[0], test.index.values[test.shape[0] - 1])
            y_prd = np.exp(y_prd)
            rs_hlw_log = sqrt(mean_squared_error(test[col].values, y_prd))
            print(rs_hlw_log)
            dict_rmse["rs_hlw_log"] = rs_hlw_log
            insert_into_database("HOLT_WINTER", rs_hlw_log, "{}")


    except Exception as e:
        print(("error in HOLT winter forecasting,{}".format(e)))
        insert_into_database("HOLT_WINTER", None, e)
    # ARIMA MODEL....

    # try:
    #     rs = test_stationary(df, col)
    #     if rs:
    #
    #         # Here we decide the order of diffrencing the Time Series
    #         df_diff = df - df.shift()
    #         df_diff.dropna(inplace=True)
    #         rs = test_stationary(df_diff, col)
    #         if rs:
    #             df_diff = df_diff - df_diff.shift()
    #
    #     df_diff.dropna(inplace=True)
    #
    #     train, test = train_test_split(df_diff)
    #
    #     """ The acf and pacf plots are
    #         used to calculate the the parametre for AR
    #         AND MA MODELS"""
    #
    #     ar_list = get_params_p(train)
    #     ma_list = get_params_q(train)
    #
    #     for i in ma_list:
    #         for j in ar_list:
    #             try:
    #                 model = ARIMA(train, order=(j, 0, i)).fit()
    #                 y_prd = model.predict(start=test.index.values[0], end=test.index.values[test.shape[0] - 1])
    #
    #                 rs = sqrt(mean_squared_error(test[col].values, y_prd))
    #                 insert_into_database("ARIMA", rs, "{}")
    #             except Exception as e:
    #
    #                 print(("error while training arima,{}".format(e)))
    #                 insert_into_database("ARIMA", None, e)
    # except Exception as e:
    #
    #     print(("error in arima model,{}".format(e)))
    #     insert_into_database("ARIMA", None, e)




    # .. SARIMAX
    try:
        train, test = train_test_split(df)
        p = d = q = list(range(0, 2))
        non_seas = list(itertools.product(p, d, q))
        lis = [1, 3, 6, 12, 24, 56]

        for i in lis:
            sea_so = [(x[0], x[1], x[2], i) for x in list(itertools.product(p, d, q))]

            for j in non_seas:
                for k in sea_so:
                    try:
                        model = SARIMAX(train, order=j, seasonal_order=k, enforce_stationarity=
                        False, enforce_invertibility=False).fit()
                        y_prd = model.predict(start=test.index.values[0],
                                              end=test.index.values[test.shape[0] - 1])

                        rs = sqrt(mean_squared_error(test.values, y_prd))

                        print(rs)
                        insert_into_database("SARIMAX", rs, "{}")
                    except Exception as e:
                        print(("error while training the SARIMAX MODELS,{}".format(e)))
                        insert_into_database("SARIMAX", None, e)

    except Exception as e:
        print(("error in seasonal_arima,{}".format(e)))
        insert_into_database("SARIMAX", None, e)

    # ..AUTO_ARIMA..

    try:
        train, test = train_test_split(df)
        model = auto_arima(train, start_p=1, start_q=1, start_P=1, start_Q=1, max_p=5
                           , max_q=5, max_P=5, max_Q=1, d=1, D=1, seasonal=True)
        model = model.fit(train)
        y_prd = model.predict(n_periods=len(test))
        rs = sqrt(mean_squared_error(test.values, y_prd))
        print("results in auto_Arima", rs)
        dict_rmse["auto_arima"] = rs
        insert_into_database("AUTO_ARIMA", rs, "{}")


    except Exception as e:

        print("error in auto_Arima,{}".format(e))
        insert_into_database("Auto_arima", None, e)

    # ALL MODELS FOR TIME SERIES ARE ADDED
