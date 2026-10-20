"""Run from the blog5 folder: python code/analyze.py [--refresh]."""
import json, sys, urllib.request, pathlib, math
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
ROOT=pathlib.Path(__file__).resolve().parents[1]
for sub in ['data/raw','data/processed','results/figures']:(ROOT/sub).mkdir(parents=True,exist_ok=True)
urls={
'acs2024_5yr.json':'https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B25064,B25070&geo_ids=140%7C05000US42101',
 'tracts_tiger2024.geojson':'https://api.censusreporter.org/1.0/geo/show/tiger2024?geo_ids=140%7C05000US42101'}
for filename,url in urls.items():
 path=ROOT/'data/raw'/filename
 if '--refresh' in sys.argv or not path.exists():
  with urllib.request.urlopen(url,timeout=60) as response: content=response.read()
  json.loads(content) # Never replace cached data with an HTML error page.
  path.write_bytes(content)
x=json.loads((ROOT/'data/raw/acs2024_5yr.json').read_text()); geo=json.loads((ROOT/'data/raw/tracts_tiger2024.geojson').read_text())
assert x['release']['id']=='acs2024_5yr'
rows=[]
for geoid,v in x['data'].items():
 a=v['B25070']['estimate']; total=a['B25070001']; nc=a['B25070011']
 valid=total-nc if total is not None and nc is not None else None
 parts=[a[f'B25070{i:03}'] for i in range(7,11)]
 burden_count=sum(parts) if all(z is not None and z>=0 for z in parts) else None
 rent=v['B25064']['estimate']['B25064001']
 rows.append(dict(geoid=geoid,rent=rent if rent and rent>0 else None,total=total,not_computed=nc,valid=valid,burden_count=burden_count,severe_count=a['B25070010'],burden=100*burden_count/valid if valid and burden_count is not None else None))
df=pd.DataFrame(rows); assert df.geoid.is_unique
features={f['properties']['geoid']:f for f in geo['features']}
assert set(df.geoid)==set(features), 'Boundary/data GEOID mismatch'
assert df.burden.dropna().between(0,100).all()
# 100 is an estimated household count, NOT a survey sample-size cutoff.
df['eligible']=df.rent.notna() & df.burden.notna() & (df.valid>=100)
s=df[df.eligible].copy();cut=s.rent.median();s['rent_group']=s.rent.ge(cut).map({False:'Lower-rent half',True:'Higher-rent half'})
groups=[]
for name,z in s.groupby('rent_group',sort=False):
 groups.append(dict(group=name,tracts=len(z),eligible_households=z.valid.sum(),burdened_households=z.burden_count.sum(),burden_pct=100*z.burden_count.sum()/z.valid.sum(),median_tract_rent=z.rent.median()))
summary=dict(period=x['release']['years'],all_tracts=len(df),eligible_tracts=len(s),excluded_tracts=len(df)-len(s),rent_split=cut,groups=groups,correlation=s.rent.corr(s.burden),examples=s[s.geoid.isin(['14000US42101003600','14000US42101000806'])].to_dict('records'),sensitivity=[])
for threshold in [0,50,100,200]:
 z=df[df.rent.notna() & df.burden.notna() & (df.valid>=threshold)].copy();c=z.rent.median()
 lo=z[z.rent<c];hi=z[z.rent>=c]
 summary['sensitivity'].append(dict(min_households=threshold,n=len(z),lower_pct=100*lo.burden_count.sum()/lo.valid.sum(),higher_pct=100*hi.burden_count.sum()/hi.valid.sum()))
df.to_csv(ROOT/'data/processed/tract_statistics.csv',index=False)
pd.DataFrame(groups).to_csv(ROOT/'results/group_summary.csv',index=False)
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titleweight':'bold'})
fig,axs=plt.subplots(1,2,figsize=(12,8),facecolor='white')
configs=[('rent',[0,1000,1250,1500,1750,10000],['Under $1,000','$1,000–1,249','$1,250–1,499','$1,500–1,749','$1,750+'],['#eff3ff','#bdd7e7','#6baed6','#3182bd','#08519c'],'Monthly gross rent'),('burden',[0,30,40,50,60,101],['Under 30%','30–39%','40–49%','50–59%','60%+'],['#fff5eb','#fdd0a2','#fdae6b','#e6550d','#a63603'],'Rent-burdened households')]
from matplotlib.patches import Patch
for ax,(var,bins,labels,colors,title) in zip(axs,configs):
 patches=[]; values=[]
 for row in df.itertuples():
  g=features[row.geoid]['geometry']; polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
  for poly in polygons:
   # Census tract polygons have no interior rings in this cached boundary set.
   assert len(poly)==1, 'Interior ring requires compound path rendering'
   patches.append(Polygon(poly[0],closed=True));values.append(getattr(row,var) if row.eligible else float('nan'))
 cmap=ListedColormap(colors);cmap.set_bad('#dedede')
 pc=PatchCollection(patches,cmap=cmap,norm=BoundaryNorm(bins,len(colors)),edgecolor='white',linewidth=.28)
 pc.set_array(values);ax.add_collection(pc);ax.autoscale_view();ax.set_aspect(1/math.cos(math.radians(40)));ax.axis('off');ax.set_title(title,pad=14)
 # Orientation references, not neighborhood boundaries.
 for lon,lat,label in [(-75.1932,39.9522,'Penn'),(-75.1636,39.9526,'City Hall')]:
  ax.plot(lon,lat,'o',ms=3,color='#111111');ax.annotate(label,(lon,lat),xytext=(-19,-13) if label=='Penn' else (4,5),textcoords='offset points',fontsize=8)
 ax.annotate('N ↑',(.93,.92),xycoords='axes fraction',fontsize=11)
 ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,labels)]+[Patch(facecolor='#dedede',label='Excluded / unavailable')],loc='lower right',frameon=False,fontsize=9)
fig.suptitle('Lower rent does not always mean a lighter burden',fontsize=19,fontweight='bold',y=.98)
fig.text(.5,.925,'Philadelphia census tracts | 2020–2024 ACS five-year estimates',ha='center',color='#555555')
fig.text(.06,.045,'Burden: 30% or more of income spent on rent and utilities, among households with a computed ratio.\nGray: unavailable rent/burden or fewer than 100 estimated households with a computed ratio.\nSource: U.S. Census Bureau, B25064 and B25070; Census Reporter TIGER 2024 boundaries.',fontsize=9,color='#555555')
fig.subplots_adjust(top=.89,bottom=.14,wspace=.06)
fig.savefig(ROOT/'results/figures/rent_burden_maps.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5.6));ax.scatter(s.rent,s.burden,s=18,c='#326b87',alpha=.52,edgecolors='none')
for geoid,label in [('14000US42101003600','Tract 36'),('14000US42101000806','Tract 8.06')]:
 row=s.set_index('geoid').loc[geoid];ax.scatter(row.rent,row.burden,c='#c55a24',s=60);ax.annotate(label,(row.rent,row.burden),xytext=(9,6),textcoords='offset points')
ax.set(xlabel='Median monthly gross rent ($)',ylabel='Rent-burdened households (%)',ylim=(0,100),title='Rent alone does not rank affordability')
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.text(.12,.01,f'Each dot is one eligible census tract (n={len(s)}); dots are not weighted by household count.\nSource: 2020–2024 ACS, tables B25064 and B25070. Descriptive comparison, not a causal estimate.',fontsize=9,color='#555555')
fig.tight_layout(rect=(0,.075,1,1));fig.savefig(ROOT/'results/figures/rent_burden_scatter.png',dpi=200);plt.close(fig)
# Quartiles classify tracts by median rent; aggregate HOUSEHOLD counts within each.
s['rent_quartile'], quartile_edges = pd.qcut(s.rent, 4, labels=False, retbins=True)
quartiles=[]
for q,z in s.groupby('rent_quartile',sort=True):
 denominator=z.valid.sum()
 severe=100*z.severe_count.sum()/denominator
 moderate=100*(z.burden_count.sum()-z.severe_count.sum())/denominator
 below=100*(z.valid.sum()-z.burden_count.sum())/denominator
 assert abs(below+moderate+severe-100)<1e-8
 quartiles.append(dict(quartile=int(q)+1,tracts=len(z),rent_min=z.rent.min(),rent_max=z.rent.max(),eligible_households=denominator,below30=below,from30to50=moderate,atleast50=severe))
summary['quartiles']=quartiles
summary['quartile_edges']=quartile_edges.tolist()
pd.DataFrame(quartiles).to_csv(ROOT/'results/quartile_burden.csv',index=False)
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2))
# Refresh the processed file with the severe-burden count added above.
df.to_csv(ROOT/'data/processed/tract_statistics.csv',index=False)
fig,ax=plt.subplots(figsize=(10,5.5))
colors=['#d9e3e8','#f6b477','#b94a23'];left=[0.0]*4
for key,color,label in zip(['below30','from30to50','atleast50'],colors,['Under 30%','30% to under 50%','50% or more']):
 vals=[q[key] for q in quartiles]
 ax.barh(range(4),vals,left=left,color=color,height=.56,label=label,edgecolor='white',linewidth=1.5)
 for i,(start,value) in enumerate(zip(left,vals)):
  ax.text(start+value/2,i,f'{value:.1f}%',ha='center',va='center',color='white' if key=='atleast50' else '#222222',fontsize=12)
 left=[a+b for a,b in zip(left,vals)]
labels=[f"{['Lowest-rent quarter','Second quarter','Third quarter','Highest-rent quarter'][i]}\nUSD {q['rent_min']:,.0f}–{q['rent_max']:,.0f}" for i,q in enumerate(quartiles)]
ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_xlim(0,100)
ax.set_xlabel('Share of renter households with a computed ratio (%)');ax.set_xticks([0,25,50,75,100])
ax.tick_params(axis='y',length=0,pad=10);ax.spines[['top','right','left']].set_visible(False)
ax.set_title('Severe rent burdens persist in lower-rent areas',loc='left',pad=48,fontsize=16)
ax.legend(loc='lower left',bbox_to_anchor=(-.015,1.04),ncol=3,frameon=False,fontsize=10,title='Rent and utilities as a share of household income',title_fontsize=10)
fig.text(.03,.015,'Groups contain approximately equal numbers of tracts, not equal numbers of households.\nLabels give tract median-rent ranges. Percentages pool household counts within each group.\nSource: 2020–2024 ACS B25064/B25070; same eligible tracts as the maps.',fontsize=9,color='#555555')
fig.tight_layout(rect=(0,.12,1,1));fig.savefig(ROOT/'results/figures/quartile_burden.png',dpi=200);plt.close(fig)

print(json.dumps(summary,indent=2))
# Generate article numbers from the same results used for the figures.
by_group={g['group']:g for g in groups}
text=(ROOT/'article_template.md').read_text()
replacements={'n':str(len(s)),'excluded':str(len(df)-len(s)),'cut':f'{cut:,.0f}','low':f"{by_group['Lower-rent half']['burden_pct']:.1f}",'high':f"{by_group['Higher-rent half']['burden_pct']:.1f}"}
for prefix, geoid in [('low','14000US42101003600'),('high','14000US42101000806')]:
 row=s.set_index('geoid').loc[geoid]
 replacements[f'example_{prefix}_rent']=f'{row.rent:,.0f}'
 replacements[f'example_{prefix}_burden']=f'{row.burden:.1f}'
for label, q in [('q1',quartiles[0]),('q4',quartiles[-1])]:
 replacements[label+'_severe']=f"{q['atleast50']:.1f}"
 replacements[label+'_moderate']=f"{q['from30to50']:.1f}"
for key,value in replacements.items():text=text.replace('{{'+key+'}}',value)
assert '{{' not in text
front='---\ntitle: "Does Lower Rent Mean Affordable Housing?"\nsubtitle: "Mapping rent and renter burdens in Philadelphia"\nauthor: "Yiran Zhang"\ndate: "2026-10-19"\ncategories: [Housing, GIS, Philadelphia]\nformat:\n  html:\n    toc: false\nexecute:\n  echo: false\n---\n\n'
(ROOT/'index.qmd').write_text(front+text)
(ROOT/'article.md').write_text('# Does Lower Rent Mean Affordable Housing?\n\n'+text)
