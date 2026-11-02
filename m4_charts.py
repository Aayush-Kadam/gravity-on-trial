"""Scientific Plotly figures; saved arrays remain unaltered."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from m4_adapter import LABELS
COLORS={'baryons':'#82d6ba','nfw':'#69b9ff','burkert':'#f2b45d','rar':'#d4a6ff','preview':'#f5da72'}
DASH={'baryons':'dot','nfw':'solid','burkert':'dash','rar':'dashdot','preview':'longdash'}
def polish(fig,title='',height=480):
    fig.update_layout(template='plotly_dark',title=title,height=height,paper_bgcolor='#0f172a',plot_bgcolor='#0f172a',font=dict(family='Arial',size=13,color='#f1f5f9'),margin=dict(l=62,r=24,t=52,b=48),legend=dict(orientation='h',y=1.03,x=0,font=dict(size=11)),hovermode='x unified')
    fig.update_xaxes(showgrid=True,gridcolor='#26364a',zerolinecolor='#64748b');fig.update_yaxes(showgrid=True,gridcolor='#26364a',zerolinecolor='#64748b');return fig
def rotation(b,records,components=False):
    f=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[.7,.3],vertical_spacing=.08)
    x=b['radius_kpc'];obs=np.array(b['observed_km_s']);err=np.array(b['error_km_s'])
    f.add_trace(go.Scatter(x=x,y=obs.tolist(),name='Observed · SPARC',mode='markers',marker=dict(color='#f8fafc',size=5,symbol='circle'),error_y=dict(type='data',array=err.tolist(),color='#cbd5e1',thickness=1,width=2)),row=1,col=1)
    for key,r in records.items():
        if 'prediction_km_s' not in r:continue
        y=np.array(r['prediction_km_s']); label=LABELS.get(key,key)
        for row,values in [(1,y),(2,(y-obs)/err)]:
            f.add_trace(go.Scatter(x=x,y=values.tolist(),name=label,legendgroup=key,showlegend=row==1,mode='lines',line=dict(color=COLORS.get(key,'#f5da72'),dash=DASH.get(key,'longdash'),width=2)),row=row,col=1)
    f.add_hline(y=0,line_color='#94a3b8',line_width=1,row=2,col=1)
    f.update_yaxes(title_text='Catalog-frame velocity (km/s)',row=1,col=1);f.update_yaxes(title_text='(model − obs) / σ',row=2,col=1);f.update_xaxes(title_text='Catalog radius (kpc)',row=2,col=1)
    return polish(f,height=550)
def components(b):
    f=go.Figure(); x=b['radius_kpc']
    for name,key,scale,color,dash in [('Gas · signed','gas_signed_km_s',1,'#d4a6ff','solid'),('Disk · Υ=0.5','disk_unit_ML_km_s',.5**.5,'#69b9ff','dash'),('Bulge · Υ=0.7','bulge_unit_ML_km_s',.7**.5,'#f2b45d','dot')]:
        f.add_trace(go.Scatter(x=x,y=[v*scale for v in b[key]],name=name,line=dict(color=color,dash=dash)))
    f.update_xaxes(title='Catalog radius (kpc)');f.update_yaxes(title='Signed equivalent speed (km/s)');return polish(f,'Published mass components · negative gas retained',320)
