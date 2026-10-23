"""PSID father-son matching with SQLite. Run from any directory."""
from pathlib import Path
import re,sqlite3,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; OUT=ROOT/'results'; (OUT/'figures').mkdir(parents=True,exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
extract=max((p for p in RAW.glob('J*.do') if not p.name.endswith('_formats.do')), key=lambda p:p.stat().st_mtime)
setup=extract.read_text()
spec=re.findall(r'(ER\d+|V\d+)\s+(\d+)\s*-\s*(\d+)',setup.split('infix',1)[1].split('using',1)[0])
names=[x[0] for x in spec]
cache=ROOT/'data'/f'{extract.stem}.pkl'
if cache.exists(): df=pd.read_pickle(cache)
else:
 df=pd.read_fwf(extract.with_suffix('.txt'),colspecs=[(int(a)-1,int(b)) for _,a,b in spec],names=names,dtype=float)
 df.to_pickle(cache)
labels=dict(re.findall(r'label variable\s+(\w+)\s+"([^"]+)"',setup))
years=list(range(1968,1998))+list(range(1999,2024,2))
income_vars='V1191 V1892 V2493 V3046 V3458 V3858 V4373 V5283 V5782 V6391 V6981 V7573 V8265 V8873 V10256 V11397 V12796 V13898 V14913 V16413 V17829 V19129 V20429 V21739 ER4122 ER6962 ER9213 ER12196 ER16493 ER20425 ER24117 ER27913 ER40903 ER46811 ER52219 ER58020 ER65200 ER71277 ER77299 ER81626 ER85480'.split()
years=[y for y in years if y>=1970]
assert len(years)==len(income_vars)
def find_var(prefix,y):
 yy=str(y)[-2:]
 return next(k for k,v in labels.items() if v.startswith(prefix) and v.rstrip().endswith(yy))
cpi=pd.read_csv(RAW/'cpi_official.csv');cpi=cpi[pd.to_numeric(cpi.Year,errors='coerce').notna()];cpi=dict(zip(cpi.Year.astype(int),cpi['Annual Average Index']))
people=pd.DataFrame({'family_id':df.ER30001.astype(int),'person_no':df.ER30002.astype(int),'sex':df.ER32000.astype(int),'father_family_id':df.ER32016.astype(int),'father_person_no':df.ER32017.astype(int)})
people['person_id']=people.family_id*1000+people.person_no
assert people.person_id.is_unique
long=[];mapping=[]
for y,inc in zip(years,income_vars):
 age=find_var('AGE OF INDIVIDUAL',y)
 rel=next(k for k,v in labels.items() if v.startswith(('RELATIONSHIP TO HEAD','RELATION TO HEAD','RELATION TO REFERENCE')) and v.rstrip().endswith(str(y)[-2:]))
 seq=find_var('SEQUENCE NUMBER',y) if y>1968 else None
 fam='ER30001' if y==1968 else next(k for k,v in labels.items() if v==f'{y} INTERVIEW NUMBER')
 head=(df[rel]==(1 if y<1983 else 10))
 resident=(df[seq].between(1,20)) if seq else pd.Series(True,index=df.index)
 earnings=df[inc]
 # Top-code endpoints are excluded rather than treated as exact earnings.
 valid=head&resident&df[fam].gt(0)&df[age].between(18,90)&earnings.gt(0)&~earnings.isin([99999,999999,9999999,9999998,99999999])
 t=pd.DataFrame({'person_id':people.person_id[valid],'wave':y,'income_year':y-1,'age':df.loc[valid,age]-1,'earnings':earnings[valid]*float(cpi[2022])/float(cpi[y-1]),'family_interview':df.loc[valid,fam]})
 long.append(t);mapping.append({'wave':y,'income_year':y-1,'income':inc,'age':age,'relationship':rel,'sequence':seq,'family_interview':fam})
long=pd.concat(long,ignore_index=True)
assert not long.duplicated(['person_id','wave']).any()
pd.DataFrame(mapping).to_csv(ROOT/'data/variable_map.csv',index=False)
conn=sqlite3.connect(ROOT/'data/analysis.sqlite')
people.to_sql('people',conn,if_exists='replace',index=False);long.to_sql('income',conn,if_exists='replace',index=False)
sql='''SELECT c.person_id AS child_id, p.person_id AS father_id
FROM people AS c
JOIN people AS p ON c.father_family_id = p.family_id
 AND c.father_person_no = p.person_no
WHERE c.sex = 1 AND p.sex = 1
 AND c.father_family_id > 0 AND c.father_person_no > 0;'''
(ROOT/'sql/01_match.sql').write_text(sql)
pairs=pd.read_sql_query(sql,conn);assert pairs.child_id.is_unique
pairs.to_sql('pairs',conn,if_exists='replace',index=False)
sql2='''WITH father AS (
 SELECT person_id, AVG(earnings) AS father_mean, COUNT(*) AS father_n,
 AVG(age) AS father_age
 FROM income WHERE age BETWEEN 35 AND 44
 GROUP BY person_id HAVING COUNT(*) >= 3
), young AS (
 SELECT person_id, AVG(earnings) AS young_mean, COUNT(*) AS young_n,
 AVG(age) AS young_age, AVG(income_year-age) AS birth_year
 FROM income WHERE age BETWEEN 25 AND 29
 GROUP BY person_id HAVING COUNT(*) >= 2
), middle AS (
 SELECT person_id, AVG(earnings) AS middle_mean, COUNT(*) AS middle_n,
 AVG(age) AS middle_age
 FROM income WHERE age BETWEEN 40 AND 44
 GROUP BY person_id HAVING COUNT(*) >= 2
)
SELECT p.*, f.father_mean, f.father_n, f.father_age,
 y.young_mean, y.young_n, y.young_age, y.birth_year,
 m.middle_mean, m.middle_n, m.middle_age
FROM pairs AS p
JOIN father AS f ON p.father_id=f.person_id
JOIN young AS y ON p.child_id=y.person_id
JOIN middle AS m ON p.child_id=m.person_id;'''
(ROOT/'sql/02_average.sql').write_text(sql2)
a=pd.read_sql_query(sql2,conn)
# Same fathers and sons in all four specifications. Single observation nearest target age,
# with earlier wave breaking an equal-distance tie.
for prefix,pid,lo,hi,target in [('father','father_id',35,44,40),('young','child_id',25,29,27),('middle','child_id',40,44,42)]:
 t=long[long.age.between(lo,hi)].copy();t['distance']=(t.age-target).abs();t=t.sort_values(['person_id','distance','wave']).drop_duplicates('person_id')
 t=t[['person_id','earnings','age','income_year']].rename(columns={'person_id':pid,'earnings':prefix+'_single','age':prefix+'_single_age','income_year':prefix+'_single_year'})
 a=a.merge(t,on=pid,validate='many_to_one')
a.to_csv(OUT/'tables/matched_sample_private.csv',index=False)

def fit(y,x,frame):
 X=np.column_stack([np.ones(len(frame)),np.log(frame[x]),(frame.birth_year-frame.birth_year.mean())/10])
 Y=np.log(frame[y]);b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b
 # Father-clustered sandwich SE allows siblings to share unobserved influences.
 score=pd.DataFrame(X*e.to_numpy()[:,None]).groupby(frame.father_id.to_numpy()).sum().to_numpy();g=len(score);n,k=X.shape
 bread=np.linalg.inv(X.T@X);v=bread@(score.T@score)@bread*g/(g-1)*(n-1)/(n-k)
 return float(b[1]),float(np.sqrt(v[1,1]))
res=[]
for age,y in [('25–29','young'),('40–44','middle')]:
 for measure in ['single','mean']:
  b,se=fit(f'{y}_{measure}',f'father_{measure}',a)
  res.append({'child_age':age,'measure':measure,'ige':b,'se':se,'low':b-1.96*se,'high':b+1.96*se,'n':len(a)})
r=pd.DataFrame(res);r.to_csv(OUT/'tables/ige_estimates.csv',index=False)
summary={'extract':extract.stem,'people':len(people),'pairs':len(pairs),'balanced_pairs':len(a),'fathers':a.father_id.nunique(),'birth_min':float(a.birth_year.min()),'birth_max':float(a.birth_year.max()),'income_records':len(long),'father_observations_median':float(a.father_n.median()),'young_observations_median':float(a.young_n.median()),'middle_observations_median':float(a.middle_n.median())}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(summary);print(r.to_string(index=False))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(8,4.7))
for j,(measure,label,color) in enumerate([('single','Single observed year','#777777'),('mean','Multiple observed years','#174C70')]):
 t=r[r.measure==measure];xx=np.arange(2)+(j-.5)*.16
 ax.errorbar(xx,t.ige,yerr=1.96*t.se,fmt='o',capsize=5,color=color,label=label,markersize=7)
ax.set_xticks([0,1],['Son aged 25–29','Son aged 40–44']);ax.set_ylabel('Estimated intergenerational earnings elasticity');ax.axhline(0,color='#ccc',lw=.8);ax.legend(frameon=False);ax.set_title('When income is measured changes the estimated link',loc='left',fontweight='bold',pad=18)
fig.text(.12,.015,f'Same {len(a):,} father–son pairs. Fathers: ages 35–44. Birth-cohort control.\n95% intervals use father-clustered standard errors. Source: PSID. Positive wages of current reference persons.',fontsize=8,color='#555')
fig.tight_layout(rect=(0,.09,1,1));fig.savefig(OUT/'figures/ige_comparison.png',dpi=180);plt.close(fig)
conn.close()
