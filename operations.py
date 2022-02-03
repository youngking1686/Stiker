import pandas as pd
import datetime as dt
import NFO_expiry_calc
from nsepython import *
import mibian

class opt_data:
    def __init__(self, instrument, expiry, side, piv, entry, stop, target):
        self.instrument = instrument
        self.expiry = expiry
        self.res = nse_optionchain_scrapper(self.instrument)['records']
        current_expiry = self.res['expiryDates'][0]
        next_expiry = self.res['expiryDates'][1]
        self.expiry_date = current_expiry if expiry == 'Current' else next_expiry
        self.side, self.piv, self.entry, self.stop, self.target =  side, piv, entry, stop, target
        self.und_prc = nse_fno('NIFTY')['underlyingValue'] if self.instrument == 'NIFTY' \
                        else nse_fno('BANKNIFTY')['underlyingValue']
        self.und = (int(50 * round(self.und_prc/50)), 50) if self.instrument == 'NIFTY' \
                    else (int(100 * round(self.und_prc/100)), 100)
    
    def make_strikes(self):
        upstks = [self.und[0]+x*self.und[1] for x in range(15)]
        dwnstks = [self.und[0]-x*self.und[1] for x in range(15)]
        return sorted(set([*upstks, *dwnstks]))
    
    def opt_dict(self, dat, option):
        no_d_ex = opt_data.days_to_expiry(self)
        c = mibian.BS([self.und_prc, dat['strikePrice'], 10, no_d_ex], volatility=dat['impliedVolatility']) #und, strike, intR, daysto expire
        reward, risk, rr = opt_data.RR_calc(self, option, dat['strikePrice'], dat['impliedVolatility'], no_d_ex)
        delta = c.callDelta if option == 'CE' else c.putDelta
        theta = c.callTheta if option == 'CE' else c.putTheta
        loc = 'ATM' if dat['strikePrice'] == self.und[0] else 'ITM' if dat['strikePrice'] < self.und[0] and option == 'CE' else \
                'ITM' if dat['strikePrice'] > self.und[0] and option == 'PE' else 'OTM'
        data = {'Strike':dat['strikePrice'],
                'Option': option,
                '%Reward':reward,
                '%Risk':risk,
                'RR':rr,
                'IV':dat['impliedVolatility'],
                'LTP':dat['lastPrice'],
                '%Change':round(dat['pChange'],2),
                'Delta':round(delta if delta else 0,2),
                'Theta':round(theta if theta else 0,2),
                'OI':dat['openInterest'],
                'Chng-OI':dat['changeinOpenInterest'],
                '%Chng-OI':round(dat['pchangeinOpenInterest'] if dat['pchangeinOpenInterest'] else 0,2),
                'Volume':dat['totalTradedVolume'],
                'Location':loc}
        return data
    
    def get_sell_opt_data(self):
        strikes = opt_data.make_strikes(self)
        opt_dt = []
        opty = 'PE' if self.side == 'Long' else 'CE'
        for recs in self.res['data']:
            if recs['expiryDate'] == self.expiry_date and recs['strikePrice'] in strikes: 
                data = opt_data.opt_dict(self, recs[opty], opty)
                opt_dt.append(data)
        return pd.DataFrame.from_dict(opt_dt)

    def get_buy_opt_data(self):
        strikes = opt_data.make_strikes(self)
        opt_dt = []
        opty = 'CE' if self.side == 'Long' else 'PE'
        for recs in self.res['data']:
            if recs['expiryDate'] == self.expiry_date and recs['strikePrice'] in strikes: 
                data = opt_data.opt_dict(self, recs[opty], opty)
                opt_dt.append(data)
        return pd.DataFrame.from_dict(opt_dt)

    def RR_calc(self, option, strike, iv_curr, no_d_ex):
        rati = abs((self.entry-self.stop)/(self.entry-self.target))
        tvola = iv_curr + (iv_curr*-1/100) if (self.piv==0 and self.side == 'Long') else iv_curr + (iv_curr*+1/100) \
            if (self.piv==0 and self.side == 'Short') else iv_curr + (iv_curr*self.piv/100)
        svola = iv_curr + (iv_curr*-1/100) if (self.piv==0 and self.side == 'Long') else iv_curr + (iv_curr*+1/100) \
            if (self.piv==0 and self.side == 'Short') else iv_curr - (iv_curr*rati*self.piv/100)
        ent = opt_data.mibi_cal(self.entry, strike, no_d_ex, iv_curr, option)
        tgt = opt_data.mibi_cal(self.target, strike, no_d_ex, tvola, option)
        stp = opt_data.mibi_cal(self.stop, strike, no_d_ex, svola, option)
        try:
            if (self.side == 'Long' and option == 'PE') or (self.side == 'Short' and option == 'CE'): #sell
                reward = (ent - tgt)*100/ent
                risk = (stp - ent)*100/ent
            elif (self.side == 'Short' and option == 'PE') or (self.side == 'Long' and option == 'CE'): #buy
                reward = (tgt - ent)*100/ent
                risk = (ent - stp)*100/ent
            return round(reward,2), round(risk,2), round(reward/risk,2)
        except:
            return 0, 0, 0
    
    @staticmethod
    def mibi_cal(und_LTP, strike, no_d_ex, vola, option):
        if option == 'CE':
            return mibian.BS([und_LTP, strike, 10, no_d_ex], volatility=vola).callPrice
        else:
            return mibian.BS([und_LTP, strike, 10, no_d_ex], volatility=vola).putPrice
    
    def days_to_expiry(self):
        if self.expiry == 'Current':
            expiry_date = NFO_expiry_calc.getNearestWeeklyExpiryDate()
        else:
            expiry_date = NFO_expiry_calc.getNextWeeklyExpiryDate()
        curr = dt.date.today()
        curr_ti = dt.datetime.now()
        return (expiry_date - curr).days + (7 - (curr_ti.hour - 9))/7

def fetch_ltp(instrument):
    return nse_fno('NIFTY')['underlyingValue'] if instrument == 'NIFTY' else nse_fno('BANKNIFTY')['underlyingValue']
