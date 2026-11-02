"""Gravity on Trial · local M4 research instrument."""
import streamlit as st
from pathlib import Path
from benchmark_setup import state
st.set_page_config(page_title='Gravity on Trial',layout='wide',initial_sidebar_state='expanded')
ready,reason=state(Path(__file__).resolve().parent)
if not ready:
    st.title('Gravity on Trial · setup required')
    st.warning(reason)
    st.write('Acquire the official SPARC sources, validate all 175 galaxies, and regenerate the full M2/M3 benchmark locally. No sample or synthetic results are substituted.')
    st.code('python benchmark_setup.py bootstrap --from-official-sources\npython benchmark_setup.py verify\n.\\Start-Gravity.ps1',language='powershell')
    st.caption('First setup requires internet for official data and approximately 10–20 minutes of serial CPU work. Checkpoints allow safe resumption. After completion, normal application use is offline.')
    st.stop()
from m4_ui import sidebar
try:
    sidebar()
except (FileNotFoundError,ValueError,KeyError) as error:
    st.error('Benchmark evidence is missing or corrupt. Run python benchmark_setup.py verify; restore the matching files or initialize a new source directory. No substitute data are loaded.')
    st.caption(str(error));st.stop()
pg=st.navigation([
    st.Page('app_pages/galaxy_lab.py',title='Galaxy lab',default=True),
    st.Page('app_pages/model_arena.py',title='Model arena'),
    st.Page('app_pages/fragility_atlas.py',title='Fragility atlas'),
    st.Page('app_pages/evidence_vault.py',title='Evidence vault')])
try:
    pg.run()
except (FileNotFoundError,ValueError,KeyError) as error:
    st.error('Benchmark evidence is missing or corrupt. Run python benchmark_setup.py verify; restore the matching files or initialize a new source directory. No substitute data are loaded.')
    st.caption(str(error))
