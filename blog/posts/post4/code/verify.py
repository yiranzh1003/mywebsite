"""Independent calculation and preview figures; run from the blog4 root."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
ROOT=Path(__file__).resolve().parents[1]
def read(s):
 d=pd.read_csv(ROOT/f'data/raw/{s}.csv',parse_dates=['observation_date'])
 return d.set_index('observation_date')[s]
p=read('CSUSHPINSA');c=read('CPIAUCSL');r=read('MORTGAGE30US').resample('MS').mean()
d=pd.concat([p.rename('price'),c.rename('cpi'),r.rename('rate')],axis=1).dropna()
assert len(d)==72 and d.index[0]==pd.Timestamp('2019-01-01') and d.index[-1]==pd.Timestamp('2024-12-01')
b=d.iloc[0]
def pay(L,rate):
 i=rate/1200
 return L*i/(1-(1+i)**-360)
d['price_index']=d.price/b.price*100
d['real_price_index']=d.price/b.price/(d.cpi/b.cpi)*100
d['payment']=pay(240000*d.price/b.price,d.rate)
d['price_only']=pay(240000*d.price/b.price,b.rate)
d['real_payment']=d.payment/(d.cpi/b.cpi)
d.to_csv(ROOT/'data/processed/monthly_analysis.csv',index_label='month')
e=d.iloc[-1]
metrics={'r0':b.rate,'r1':e.rate,'price_growth':e.price_index-100,'real_price_growth':e.real_price_index-100,'m0':d.payment.iloc[0],'m1':e.payment,'price_only':e.price_only,'payment_growth':(e.payment/d.payment.iloc[0]-1)*100,'real_payment_growth':(e.real_payment/d.payment.iloc[0]-1)*100}
(ROOT/'results/metrics.json').write_text(json.dumps(metrics,indent=2))
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
colors=['#1f537a','#c96846','#5b8d79']
def base(title,y):
 fig,ax=plt.subplots(figsize=(9,4.8));ax.set_title(title,loc='left',fontweight='bold',pad=15);ax.set_ylabel(y);ax.grid(axis='y',alpha=.2);return fig,ax
def save(fig,name,note):
 fig.text(.08,.025,note,fontsize=8,color='#555555');fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(ROOT/f'results/figures/{name}.png');plt.close(fig)
f,a=base('1. Home prices remained above their pre-pandemic level','Index (January 2019 = 100)')
a.plot(d.index,d.price_index,label='Nominal home prices',color=colors[0],lw=2.4);a.plot(d.index,d.real_price_index,label='Inflation-adjusted home prices',color=colors[1],lw=2.4);a.axhline(100,color='gray',lw=.8,ls='--');a.legend(frameon=False)
save(f,'01_prices','Source: S&P Dow Jones Indices and BLS via FRED. Case-Shiller NSA / CPI SA; monthly, 2019–2024.')
f,a=base('2. Financing became more expensive after 2021','30-year fixed mortgage rate (%)')
a.plot(d.index,d.rate,color=colors[0],lw=2.4)
save(f,'02_rates','Source: Freddie Mac via FRED. Monthly mean of available weekly rates; PMMS method changed in Nov. 2022.')
f,a=base('3. Prices and rates together increased the monthly payment','Monthly principal and interest (nominal US dollars)')
a.plot(d.index,d.payment,label='Changing prices and rates',color=colors[0],lw=2.4);a.plot(d.index,d.price_only,label='Changing prices; January 2019 rate held fixed',color=colors[1],lw=2.4,ls='--');a.legend(frameon=False)
save(f,'03_payments','Author calculations. Illustrative $300,000 home in Jan. 2019; 20% down; 360 payments. Excludes taxes/insurance.')
print(json.dumps(metrics,indent=2))
