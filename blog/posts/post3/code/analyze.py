"""Rebuild Blog 3 statistics and figures from the original IPUMS CPS extract.

Uses fixed-width positions and implied decimals from the matching IPUMS DDI.
No internet or IPUMS credentials are used during analysis.
"""
from pathlib import Path
import gzip
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
ddi = ET.parse(ROOT / 'data/cps_00001.xml')
ns = {'d': 'ddi:codebook:2_5'}
layout = pd.DataFrame([dict(variable=v.attrib['name'],
    start=int(v.find('d:location',ns).attrib['StartPos']),
    end=int(v.find('d:location',ns).attrib['EndPos']),
    implied_decimals=int(v.attrib.get('dcml',0)))
    for v in ddi.findall('.//d:var',ns)])
# Read only analytical fields; substring parsing avoids rounding long identifiers.
needed = ['YEAR','ASECFLAG','AGE','SEX','NCHILD','ASECWT','WKSWORK1','UHRSWORKLY','INCWAGE']
with gzip.open(ROOT / 'data/cps_00001.dat.gz', 'rt') as stream:
    lines = stream.read().splitlines()
df = pd.DataFrame({v: [int(line[int(row.start)-1:int(row.end)]) for line in lines]
                   for v in needed for row in layout[layout.variable.eq(v)].itertuples()})
for row in layout[layout.variable.isin(needed)].itertuples():
    if row.implied_decimals:
        df[row.variable] = df[row.variable] / 10 ** row.implied_decimals
assert df.YEAR.eq(2025).all() and df.ASECFLAG.eq(1).all()
b = df.loc[df.AGE.between(25,54) & df.SEX.isin([1,2]) & df.NCHILD.between(0,9) & (df.ASECWT>0)].copy()
assert b.WKSWORK1.between(0,52).all()
assert b.loc[b.WKSWORK1.gt(0),'UHRSWORKLY'].between(1,99).all()
assert b.loc[b.WKSWORK1.eq(0),'UHRSWORKLY'].eq(999).all()
b['gender'] = b.SEX.map({1:'Men',2:'Women'})
b['parenthood'] = np.where(b.NCHILD.gt(0),'Co-resident children','No co-resident children')
b['any_work'] = b.WKSWORK1.between(1,52)
b['part_time'] = b.UHRSWORKLY.between(1,34) & b.any_work
b['ftfy'] = b.UHRSWORKLY.between(35,99) & b.WKSWORK1.between(50,52)
b['wage_recipient'] = b.INCWAGE.between(1,99999997)
assert not (b.wage_recipient & ~b.any_work).any()
parents = ['No co-resident children','Co-resident children']
genders = ['Men','Women']
rates, means, counts = [], [], []
for par in parents:
    for gender in genders:
        x = b.loc[b.parenthood.eq(par) & b.gender.eq(gender)]
        weights = x.ASECWT
        rates.append(dict(parenthood=par,gender=gender,
            any_work_pct=100*weights[x.any_work].sum()/weights.sum(),
            part_time_among_workers_pct=100*weights[x.part_time].sum()/weights[x.any_work].sum(),
            ftfy_all_adults_pct=100*weights[x.ftfy].sum()/weights.sum()))
        counts.append(dict(parenthood=par,gender=gender,n_adults=len(x),
            n_any_work=int(x.any_work.sum()),n_wage_recipients=int(x.wage_recipient.sum()),
            n_ftfy_wage=int((x.wage_recipient & x.ftfy).sum()),
            weighted_adults=weights.sum()))
        for sample, mask in [('All wage recipients',x.wage_recipient),
                             ('Full-time, full-year',x.wage_recipient & x.ftfy)]:
            y = x.loc[mask]
            means.append(dict(sample=sample,parenthood=par,gender=gender,
                mean_income=np.average(y.INCWAGE,weights=y.ASECWT),n=len(y)))
rates,means,counts = map(pd.DataFrame,[rates,means,counts])
gaps=means.pivot(index=['sample','parenthood'],columns='gender',values='mean_income').reset_index()
gaps['gap_pct']=100*(1-gaps.Women/gaps.Men)
group_summary = counts.merge(rates, on=['parenthood','gender'], validate='one_to_one')
group_summary.to_csv(OUT/'group_summary.csv',index=False)
means.to_csv(OUT/'earnings_summary.csv',index=False)
assert counts.n_adults.sum()==55003 and counts.n_ftfy_wage.sum()==34996
assert np.isclose(gaps.loc[(gaps['sample']=='Full-time, full-year') & (gaps.parenthood==parents[1]),'gap_pct'].iloc[0],29.0140350465)
colors=['#28617c','#b96d50']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
    'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#b9c1c5',
    'axes.labelcolor':'#29343a','text.color':'#29343a','xtick.color':'#29343a','ytick.color':'#29343a',
    'savefig.facecolor':'white','axes.axisbelow':True})
xs=np.arange(2);width=.34;xt=['No co-resident\nchildren','Co-resident\nchildren']
def bars(ax,table,value,groups=genders,groupcol='gender',barcolors=colors,money=False):
    for j,g in enumerate(groups):
        vals=[table.loc[table.parenthood.eq(par)&table[groupcol].eq(g),value].iloc[0] for par in parents]
        bc=ax.bar(xs+(j-.5)*width,vals,width,color=barcolors[j],label=g)
        ax.bar_label(bc,labels=[f'${v:,.0f}' if money else f'{v:.1f}%' for v in vals],padding=5,fontsize=10)
    ax.set_xticks(xs,xt);ax.grid(axis='y',color='#e8ecee');ax.tick_params(axis='both',length=0,pad=8)
    if not money:ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
def save(fig,name,note):
    fig.text(.07,.035,note,ha='left',va='bottom',fontsize=9,color='#5c666d')
    fig.savefig(OUT/name,dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11.5,5.5))
fig.suptitle('Work patterns differ before selecting full-time workers',x=.07,ha='left',fontsize=16,fontweight='bold',y=.98)
for ax,key,title,limit in zip(axes,['any_work_pct','part_time_among_workers_pct'],
        ['Worked at any time in 2024','Usually worked fewer than 35 hours/week'],[105,25]):
    bars(ax,rates,key);ax.set_title(title,loc='left',fontsize=12,pad=18);ax.set_ylim(0,limit)
axes[0].set_ylabel('Share of all adults ages 25–54')
axes[1].set_ylabel('Share of those who worked in 2024')
axes[0].legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.13),ncol=2)
fig.subplots_adjust(left=.075,right=.98,bottom=.25,top=.75,wspace=.28)
save(fig,'work_patterns.png','Source: IPUMS CPS ASEC 2025; ASECWT-weighted. Work refers to 2024; family status to 2025.\nLeft denominator: all adults ages 25–54. Right denominator: adults with 1–52 weeks of work in 2024.')
fig,ax=plt.subplots(figsize=(9,5.8));t=means.loc[means['sample'].eq('Full-time, full-year')]
bars(ax,t,'mean_income',money=True);ax.set_ylim(0,135000);ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1000:,.0f}k'))
ax.set_ylabel('Mean annual wage and salary income (2024 dollars)')
ax.set_title('A larger earnings gap remains among selected parents',loc='left',fontweight='bold',fontsize=15,pad=38)
ax.legend(frameon=False,ncol=2,loc='lower left',bbox_to_anchor=(0,1.01))
fig.subplots_adjust(left=.12,right=.98,bottom=.24,top=.79)
save(fig,'full_time_earnings.png','Source: IPUMS CPS ASEC 2025; ASECWT-weighted; ages 25–54, positive wage income,\n35+ usual hours/week and 50–52 weeks in 2024. Children are own children of any age living in the household.')
fig,ax=plt.subplots(figsize=(9,5.8))
bars(ax,gaps,'gap_pct',groups=['All wage recipients','Full-time, full-year'],groupcol='sample',barcolors=['#707d86','#28617c'])
ax.set_ylim(0,43);ax.set_ylabel("Gap: 100 × (1 − women's mean / men's mean)")
ax.set_title('The parental earnings gap changes with the sample',loc='left',fontweight='bold',fontsize=15,pad=38)
ax.legend(frameon=False,ncol=2,loc='lower left',bbox_to_anchor=(0,1.01))
fig.subplots_adjust(left=.12,right=.98,bottom=.24,top=.79)
save(fig,'sample_comparison.png','Source: IPUMS CPS ASEC 2025; ASECWT-weighted; ages 25–54. Both samples require positive wage income.\nFull-time, full-year additionally requires 35+ hours/week and 50–52 weeks in 2024. Descriptive, not causal.')
print('Rebuilt 3 figures and 2 aggregate tables from 142,125 source records.')
print('Adult sample:',counts.n_adults.sum(),'Full-time/full-year wage sample:',counts.n_ftfy_wage.sum())

# Generate the article from the computed results so its numbers stay synchronized.
# Edit the prose template here; running this script also rewrites index.qmd.
def rate(gender, parenthood, field):
    return rates.loc[rates.gender.eq(gender)&rates.parenthood.eq(parenthood),field].iloc[0]
def pay(gender,parenthood):
    return means.loc[means.gender.eq(gender)&means.parenthood.eq(parenthood)&means['sample'].eq('Full-time, full-year'),'mean_income'].iloc[0]
def gap(parenthood,sample):
    return gaps.loc[gaps.parenthood.eq(parenthood)&gaps['sample'].eq(sample),'gap_pct'].iloc[0]
par, non = parents[1], parents[0]
ft, broad = 'Full-time, full-year', 'All wage recipients'
post = f'''---
title: "Parenthood and the Gender Earnings Gap"
author: "Yiran Zhang"
date: "2026-09-28"
format: html
image: results/work_patterns.png
---

Does the gender earnings gap become larger when people have children? A comparison of full-time workers suggests that it does. But that comparison leaves out people who reduce their hours or stop working, potentially hiding an important part of the story. To understand the pattern, we need to ask both what workers earn and who makes it into the comparison.

I use the 2025 Annual Social and Economic Supplement (ASEC) of the CPS, accessed through [IPUMS CPS](https://cps.ipums.org/). The starting sample contains {len(b):,} adults ages 25–54. Work and income refer to 2024; age and family relationships are measured in the 2025 survey. Every reported population mean and proportion uses the ASEC person weight, `ASECWT`, so observations contribute according to the population they represent.

Here, “with children” means having one's own biological, adopted, or stepchildren of any age living in the household (`NCHILD > 0`). The other group can include parents whose children live elsewhere. This is therefore a comparison by household child presence, not by whether someone has ever become a parent.

## Who is missing from a full-time comparison?

Figure 1 begins with everyone in the age group, including people without wage income. The left panel shows the share who worked at least one week in 2024. The right panel asks, among those who worked, how many usually worked fewer than 35 hours per week. These different denominators distinguish not working from working part-time; neither measure is the official survey-week employment rate.

![Annual work participation and part-time work by sex and presence of own children.](results/work_patterns.png){{#fig-work width=100%}}

With co-resident children, {rate('Women',par,'any_work_pct'):.1f}% of women worked during the year, compared with {rate('Men',par,'any_work_pct'):.1f}% of men. Among those who worked, {rate('Women',par,'part_time_among_workers_pct'):.1f}% of women usually worked part-time, versus {rate('Men',par,'part_time_among_workers_pct'):.1f}% of men. Without co-resident children, the differences are smaller: annual work rates are {rate('Women',non,'any_work_pct'):.1f}% and {rate('Men',non,'any_work_pct'):.1f}%, respectively. The work measures include self-employed and unpaid family workers as well as employees.

A full-time-only comparison removes part-time workers from view, while requiring year-round work also excludes people who work for only part of the year. Similar hours within the remaining sample cannot establish that work time is unimportant.

## What do the workers who remain earn?

Now restrict the comparison to positive-wage recipients who usually worked at least 35 hours per week for 50–52 weeks. This leaves {counts.n_ftfy_wage.sum():,} people. Figure 2 shows their weighted mean annual pre-tax wage and salary income, in 2024 dollars. It measures annual wage income, not hourly pay or total earnings from every source.

![Weighted mean annual wage income among full-time, full-year wage recipients.](results/full_time_earnings.png){{#fig-income width=100%}}

Without co-resident children, men's mean income is \\${pay('Men',non):,.0f} and women's is \\${pay('Women',non):,.0f}. With co-resident children, the means are \\${pay('Men',par):,.0f} and \\${pay('Women',par):,.0f}. Higher male mean earnings across the two groups account for much of the larger parental gap. That is a descriptive comparison, not evidence that parenthood itself raises men's pay: age, occupation, education, and other characteristics also differ.

## How much does the sample matter?

Figure 3 compares that restricted sample with all positive-wage recipients, including part-time and part-year workers. The gap is 100 × (1 − women's weighted mean / men's weighted mean).

![Gender wage-income gaps under two sample definitions. Both require positive wage income.](results/sample_comparison.png){{#fig-gap width=100%}}

With co-resident children, the gap is {gap(par,ft):.1f}% among full-time, full-year workers but {gap(par,broad):.1f}% among all wage recipients. Without co-resident children, it changes only from {gap(non,ft):.1f}% to {gap(non,broad):.1f}%. The larger change for parents is consistent with the work-pattern differences in Figure 1. It is not a causal decomposition, and neither earnings sample includes people with zero wage income.

The lesson is that sample selection changes the question being answered. Income among full-time workers describes one part of the parental gender gap; participation and working time reveal another. These cross-sectional data cannot identify a causal motherhood penalty, especially because family status is observed after the income year. Income imputation and topcoding also affect measurement, and no survey-design confidence intervals are estimated. The figures describe weighted patterns, not statistically established causal effects.

## Sources

Data: [IPUMS CPS](https://cps.ipums.org/), 2025 ASEC. Variable documentation: [NCHILD](https://cps.ipums.org/cps-action/variables/NCHILD), [WKSWORK1](https://cps.ipums.org/cps-action/variables/WKSWORK1), [UHRSWORKLY](https://cps.ipums.org/cps-action/variables/UHRSWORKLY), [INCWAGE](https://cps.ipums.org/cps-action/variables/INCWAGE), and [ASECWT](https://cps.ipums.org/cps-action/variables/ASECWT). Code, data access, and replication instructions are documented in `README.md`.
'''
(ROOT/'index.qmd').write_text(post,encoding='utf-8')
print('Updated the Quarto article from the computed estimates.')
