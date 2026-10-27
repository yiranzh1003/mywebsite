"""Rebuild charts and result tables from the bundled historical snapshot."""
from pathlib import Path
import json
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
df = pd.read_csv(ROOT / 'data/gapminder.csv')
assert len(df) == 1704 and df.country.nunique() == 142
assert not df.duplicated(['country', 'year']).any()
assert not df[['gdpPercap', 'lifeExp', 'pop']].isna().any().any()
assert (df[['gdpPercap', 'lifeExp', 'pop']] > 0).all().all()
assert df.groupby('country').size().eq(12).all()
labels = {'gdpPercap':'GDP per capita (inflation-adjusted US$, log scale)',
          'lifeExp':'Life expectancy at birth (years)', 'pop':'Population', 'continent':'Continent'}
fig = px.scatter(df, x='gdpPercap', y='lifeExp', size='pop', color='continent',
 animation_frame='year', animation_group='country', hover_name='country',
 hover_data={'gdpPercap':':,.0f', 'lifeExp':':.1f', 'pop':':,', 'year':True},
 log_x=True, size_max=52, range_x=[200,150000], range_y=[20,90],
 labels=labels, template='plotly_white', color_discrete_sequence=px.colors.qualitative.Safe)
fig.update_layout(height=620, margin=dict(l=65,r=25,t=30,b=60), legend=dict(title='Click continent to hide/show',orientation='h',y=1.12,x=0),font=dict(size=13))
fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration']=900
fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration']=350
countries=['China','Costa Rica','United States','South Africa']
trail=go.Figure()
for country in countries:
 d=df[df.country.eq(country)]
 trail.add_trace(go.Scatter(x=d.gdpPercap,y=d.lifeExp,mode='lines+markers+text',
 text=d.year.astype(str),textposition='top center',name=country,
 customdata=d[['year','pop']].to_numpy(),
 hovertemplate=country+'<br>Year: %{customdata[0]:.0f}<br>GDP per capita: $%{x:,.0f}<br>Life expectancy: %{y:.1f} years<extra></extra>'))
trail.update_layout(template='plotly_white',height=540,xaxis=dict(title=labels['gdpPercap'],type='log',range=[2.5,4.8]),yaxis=dict(title=labels['lifeExp'],range=[35,85]),margin=dict(l=65,r=25,t=50,b=60),legend=dict(orientation='h',y=1.12),font=dict(size=13))
# Dropdown changes all trace visibility explicitly; selection never leaves stale traces.
buttons=[dict(label='Compare all four',method='update',args=[{'visible':[True]*4}])]
buttons += [dict(label=c,method='update',args=[{'visible':[v==c for v in countries]}]) for c in countries]
trail.update_layout(updatemenus=[dict(buttons=buttons,x=0,y=1.27,xanchor='left')])
summary=df[df.country.isin(countries)&df.year.isin([1952,1992,2007])][['country','year','gdpPercap','lifeExp']]
summary.to_csv(OUT/'country_summary.csv',index=False)
metrics={'observations':len(df),'countries':df.country.nunique(),'years':sorted(df.year.unique().tolist()),'plotly_version':plotly.__version__}
(OUT/'validation.json').write_text(json.dumps(metrics,indent=2))
config={'responsive':True,'displaylogo':False,'scrollZoom':False}
a=fig.to_html(full_html=False,include_plotlyjs=False,div_id='world-chart',config=config)
b=trail.to_html(full_html=False,include_plotlyjs=False,div_id='country-chart',config=config)
# Explicit raw HTML fences prevent Plotly's indentation becoming Markdown code blocks.
for name,widget in [('_world_chart',a),('_country_chart',b)]:
 (OUT/(name+'.md')).write_text('```{=html}\n<script>'+get_plotlyjs()+'</script>\n'+widget+'\n```\n')
print('Created interactive widgets and result tables.')
