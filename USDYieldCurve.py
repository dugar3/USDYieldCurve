#!/usr/bin/env python
# coding: utf-8

# In[27]:


class USDYieldCurve:
    from datetime import date
    from datetime import timedelta
    import datetime
    import calendar
    import numpy as np
    from dateutil.relativedelta import relativedelta
    
    def __init__(self, depoRates_file, futurePrices_file, tradeDate_file, holidayCalendar_file):
        depo_file = open(depoRates_file, 'r') 
        depoRates = depo_file.readlines()

        futures_file = open(futurePrices_file, 'r')
        futurePrices = futures_file.readlines()

        trade_file = open(tradeDate_file, 'r')
        tradeDate = trade_file.readlines()

        holiday_file = open(holidayCalendar_file, 'r')
        holidayCalendar = holiday_file.readlines()
        
        # Read and store the series of annualized cash deposit rates
        depoRates2 = []
        for deposit in depoRates:
            currency = deposit[0:3]
            time_to_maturity = int(deposit[3])
            period_to_maturity = deposit[4]
            s1, s2 = deposit.split()
            rate = float(s2)
            depoRates2.append([currency, time_to_maturity, period_to_maturity, rate])
            
        # Read and store the trade date
        tradeDate2 = self.date.fromisoformat(tradeDate[0].split()[0])
        
        self.tradeDate = tradeDate2
        
        # Read and store the future prices
        futurePrices2 = []
        for future in futurePrices:
            pair = future[0:2]
            month = future[2]
            year = (tradeDate2.year - tradeDate2.year%10) + int(future[3])
            if(year < tradeDate2.year):
                year += 10
            s1, s2 = future.split()
            price = float(s2)
            futurePrices2.append([pair, month, year, price])
        
        # Read and store the holiday calendar
        holidayCalendar2 = []
        for holiday in holidayCalendar:
            holidayCalendar2.append(self.date.fromisoformat(holiday.split()[0]))
        
        # Helper functions:
        ## Checks if day is the last of the month
        def last_day_of_month(date):
            last_day_of_month = self.calendar.monthrange(date.year, date.month)[1]
            if date == self.datetime.date(date.year, date.month, last_day_of_month):
                return True
            return False

        ## Checks if day is a weekend or Fed holiday
        def is_fed_holiday(date):
            if (date in holidayCalendar2):
                return True
            elif (date.weekday() >= 5):
                return True
            else:
                return False
        
        # Calculate the spot date
        def spot_date(from_date):
            business_days_to_add = 2
            current_date = from_date
            while business_days_to_add > 0:
                current_date += self.timedelta(days=1)
                if is_fed_holiday(current_date): 
                    continue
                business_days_to_add -= 1
            return current_date
        s = spot_date(tradeDate2)

        # Initialize the discount curve
        discount_curve = []
        
        # Futures expire on the 3rd Wednesday of each month
        def third_wednesday(year, month):
            third = self.datetime.date(year, month, 15)
            w = third.weekday()
            if w != 2:
                # Replace the day of the month
                third = third.replace(day=(15 + (2 - w) % 7))
            return third
        
        # Discount Curve from Cash deposits
        for i in depoRates2:
            # Calculation of the expiry date
            expiry = s
            if i[2] == 'D':
                expiry += self.datetime.timedelta(days = i[1])
            if i[2] == 'W':
                expiry += self.datetime.timedelta(weeks = i[1])
            if i[2] == 'M':
                if last_day_of_month(expiry):
                    expiry += self.relativedelta(months=+i[1])
                    expiry = self.datetime.date(expiry.year, expiry.month, self.calendar.monthrange(expiry.year, expiry.month)[-1])
                else:
                    expiry += self.relativedelta(months=+i[1])
            while is_fed_holiday(expiry):
                expiry += self.datetime.timedelta(days = 1)

            # calculation of the rate
            rate = i[3]/100.0

            # calculation of df
            delta = expiry - s
            df = 1.0/(1+rate*delta.days/360.0)

            discount_curve.append([expiry, rate, df])
            
        # Discount curve from futures
        futures_partial = []
        for i, val in enumerate(futurePrices2):
            # expiry calculation of 3rd wednesday of the month:
            months = {'H':3, 'M':6, 'U':9, 'Z':12}
            expiry = third_wednesday(val[2], months[val[1]])

            while is_fed_holiday(expiry):
                expiry += self.datetime.timedelta(days = 1)

            # calculation of the rate:
            rate = 1.0-val[3]/100.0


            futures_partial.append([expiry, rate])

        futures_df = []
        for i, val in enumerate(futures_partial):
            if i == 0:
                depo_deltas = []
                for j, val2 in enumerate(discount_curve):
                    delta = val2[0]-val[0]
                    depo_deltas.append(delta.days)
                try:
                    under_index = depo_deltas.index(max([n for n in depo_deltas if n<0]))
                    over_index = depo_deltas.index(min([n for n in depo_deltas if n>0]))
                except ValueError:
                    print("Insufficient LIBOR cash rate data")
                d1 = discount_curve[under_index][0]
                d2 = discount_curve[over_index][0]
                df1 = discount_curve[under_index][2]
                df2 = discount_curve[over_index][2]
                d = val[0]


                df = self.np.exp(self.np.log(df1) + (self.np.log(df2)-self.np.log(df1))*(d-d1).days/(d2-d1).days)

                futures_df.append(df)
            else:
                futures_df.append(futures_df[i-1]/(1+futures_partial[i-1][1]*(val[0]-futures_partial[i-1][0]).days/360.0))

        for i, val in enumerate(futures_df):
            discount = futures_partial[i]
            discount.append(val)
            discount_curve.append(discount)
        discount_curve.sort()
        
        # Set Object Parameters
        self.discount_curve = discount_curve
        self.s = s
        
    # This method get a discount factor of a given day, based on the discount curve
    def getDfToDate(self, d):
        d = self.date.fromisoformat(d)
        depo_deltas = []
        for val in self.discount_curve:
            delta = val[0]-d
            depo_deltas.append(delta.days)
        
        try:
            under_index2 = depo_deltas.index(max([n for n in depo_deltas if n<0]))
            over_index2 = depo_deltas.index(min([n for n in depo_deltas if n>0]))
        except ValueError:
                return("Cannot compute discount factor for given date")
        
        d1 = self.discount_curve[under_index2][0]
        d2 = self.discount_curve[over_index2][0]
        
        df1 = self.discount_curve[under_index2][2]
        
        df2 = self.discount_curve[over_index2][2]

        df = self.np.exp(self.np.log(df1) + (self.np.log(df2)-self.np.log(df1))*(d-d1).days/(d2-d1).days)

        return(df)
    
    # This method gets the forward rate between 2 dates
    def getFwdRate(self, d1, d2):
        df1 = self.getDfToDate(d1)
        df2 = self.getDfToDate(d2)

        d1 = self.date.fromisoformat(d1)
        d2 = self.date.fromisoformat(d2)
        if (d1 < self.s or d1 >= d2):
            return('Cannot compute the forward rate between the given dates')
        try:
            rf = 360.0/(d2-d1).days*(df1/df2 - 1)
        except TypeError:
            return('Cannot compute the forward rate between the given dates')
        return(rf)

