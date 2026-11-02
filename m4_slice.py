"""NGC3198 gate: no population-module expansion until validated."""
import streamlit as st
from m4_adapter import *
from m4_charts import rotation,components
st.set_page_config(page_title='Gravity on Trial · vertical slice',layout='wide')
st.title('Galaxy lab · NGC3198')
st.caption('OBSERVED · SPARC | VALIDATED RESULT · M2-v1 | INTERACTIVE PREVIEW · halo removal')
b=read(baseline_path('NGC3198'))
st.write(b['metadata'])
selected=st.multiselect('Models',MODELS,default=MODELS,format_func=lambda m:LABELS[m])
def restore():st.session_state['remove']=False
remove=st.toggle('Remove dark matter',key='remove')
st.button('Restore original configuration',on_click=restore)
records={m:result(b,m) for m in selected}
if remove:records={'preview':remove_halo(b,result(b,'nfw'))};st.warning('INTERACTIVE PREVIEW · halo removed at the same stellar and geometry assumptions. No refit; observations and uncertainties unchanged.')
st.plotly_chart(rotation(b,records),theme=None)
st.plotly_chart(components(b),theme=None)
st.dataframe(score_rows([result(b,m) for m in selected]))
st.dataframe(parameter_rows([result(b,m) for m in selected]))
st.download_button('Download numerical CSV',csv_bytes(table(b,records)),'NGC3198.csv','text/csv')
st.json(provenance(b),expanded=False)
