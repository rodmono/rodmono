# -*- coding: utf-8 -*-
#######################################
#-------------------------------------#
# Module: marketdata     		      #
#-------------------------------------#
# Creado:			                  #
# 12. Jul. 2022                       #
# Ult. modificacion:                  #
# 15. Jul. 2022                       #
#-------------------------------------#
# Author: rodmono                     #
#-------------------------------------#
#-------------------------------------#
#-------------------------------------#
#######################################
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
import datetime as dt
import time
from functools import reduce
import matplotlib.pyplot as plt
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import warnings
warnings.filterwarnings('ignore')

# Global variables
class CoinGeckoNew:

    def __init__( self, _CoinGeckoAPI_ ):
        self.CoinGeckoAPI = _CoinGeckoAPI_

    def __request(self, url):
        # print(url)
        try:
            response = self.CoinGeckoAPI.session.get(url, timeout=self.CoinGeckoAPI.request_timeout)
        except requests.exceptions.RequestException:
            raise

        try:
            response.raise_for_status()
            content = json.loads(response.content.decode('utf-8'))
            return content
        except Exception as e:
            # check if json (with error message) is returned
            try:
                content = json.loads(response.content.decode('utf-8'))
                raise ValueError(content)
            # if no json
            except json.decoder.JSONDecodeError:
                pass

            raise

    def __api_url_params(self, api_url, params, api_url_has_params=False):
        if params:
            # if api_url contains already params and there is already a '?' avoid
            # adding second '?' (api_url += '&' if '?' in api_url else '?'); causes
            # issues with request parametes (usually for endpoints with required
            # arguments passed as parameters)
            api_url += '&' if api_url_has_params else '?'
            for key, value in params.items():
                if type(value) == bool:
                    value = str(value).lower()

                api_url += "{0}={1}&".format(key, value)
            api_url = api_url[:-1]
        return api_url

    def get_coin_market_chart_by_id_fixed(self, id, vs_currency, days, **kwargs):
        """Get historical market data include price, market cap, and 24h volume (granularity daily)"""

        api_url = '{0}coins/{1}/market_chart?vs_currency={2}&days={3}&interval=daily'.format(self.CoinGeckoAPI.api_base_url, id, vs_currency, days)
        api_url = self.__api_url_params(api_url, kwargs, api_url_has_params=True)

        return self.__request(api_url)

cg_api    = CoinGeckoAPI()
cg_api_n  = CoinGeckoNew( cg_api )
coin_dict = pd.DataFrame(cg_api.get_coins_list())

class HistoricalMarketData:

    def __init__( self, token, currency, start_date, end_date ):
        self.token_list = token
        self.currency   = currency
        start_date      = int(time.mktime(dt.datetime.strptime(start_date, "%Y-%m-%d").timetuple()))
        self.start_date = start_date
        end_date        = int(time.mktime(dt.datetime.strptime(end_date, "%Y-%m-%d").timetuple()))
        self.end_date   = end_date

    def hist_mkt_data( self, feature ):
        if type(self.token_list) == list:
            hist_data = []
            for tkn in self.token_list:
                hist_tkn = cg_api.get_coin_market_chart_range_by_id(tkn,self.currency,self.start_date,self.end_date)[feature]
                hist_tkn = pd.DataFrame(hist_tkn,columns=["date",tkn])
                hist_tkn.date = pd.to_datetime(hist_tkn.date,unit='ms')
                hist_tkn = hist_tkn.set_index("date",True)
                hist_data.append(hist_tkn)
            df_data = pd.concat(hist_data,axis=1)
            df_data.index.name = None
            return df_data
        elif type(self.token_list) == str:
            hist_tkn = cg_api.get_coin_market_chart_range_by_id(self.token_list,self.currency,self.start_date,self.end_date)[feature]
            hist_tkn = pd.DataFrame(hist_tkn,columns=["date",self.token_list])
            hist_tkn.date = pd.to_datetime(hist_tkn.date,unit='ms')
            hist_tkn = hist_tkn.set_index("date",True)
            hist_tkn.index.name = None
            return hist_tkn

    def price( self ):
        return self.hist_mkt_data( "prices" )

    def volume( self ):
        return self.hist_mkt_data( "total_volumes" )

    def market_cap( self ):
        return self.hist_mkt_data( "market_caps" )

    def all_data( self ):
        if type(self.token_list) == list:
            df1 = self.hist_mkt_data( "prices" )
            df2 = self.hist_mkt_data( "total_volumes" )
            df3 = self.hist_mkt_data( "market_caps" )
            df4 = pd.concat([df1,df2,df3],axis=1)
            cols = [("price",tkn) for tkn in self.token_list] + [("volume",tkn) for tkn in self.token_list] + [("market_cap",tkn) for tkn in self.token_list]
            df4.columns = pd.MultiIndex.from_tuples(cols)
            df4 = df4.swaplevel(i=0, j=1, axis=1)
            df4.sort_index(axis=1, level=0, inplace=True)
            return df4
        elif type(self.token_list) == str:
            df1 = self.hist_mkt_data( "prices" )
            df2 = self.hist_mkt_data( "total_volumes" )
            df3 = self.hist_mkt_data( "market_caps" )
            final = pd.concat([df1,df2,df3],axis=1)
            columns = [(self.token_list,'price'),(self.token_list,'volume'),(self.token_list,'market_cap')]
            final.columns = pd.MultiIndex.from_tuples(columns)
            return final

class GasPrice:

    def __init__( self, start_date, end_date ):
        # This is linked to my metamask
        API_KEY    = "252fe4d058bf4257bd76b7b4a66339df"
        API_SECRET = "cd9ed3491d4f4a35abf4dbc051058f08"
        # Create url
        url = 'https://owlracle.info/eth/history?'
        url = url + 'apikey={api_key}&to={to}&candles={candles}&timeframe={timeframe}&'
        url = url + 'from={from}&tokenprice={token_price}&txfee={txn_fee}'
        params = {
            'api_key'     : API_KEY,
            'from'        : int(start_date),
            'to'          : int(end_date),
            'candles'     : 100,
            'timeframe'   : 30,
            'token_price' : 'true',
            'txn_fee'      : 'true'
        }

        url = url.format(**params)
        resp = requests.get(url=url)
        data = resp.json()
        self.gas_data = pd.DataFrame(data)
        

