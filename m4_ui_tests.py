"""Actual Streamlit session execution; browser evidence is recorded separately."""
import json,time
from pathlib import Path
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest
from m4_adapter import ROOT,json_bytes
out=ROOT/'results/m4/v1';report={};start=time.perf_counter()
a=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=25).run();assert not a.exception
assert len(a.selectbox(key='galaxy').options)==175
report['catalog_175']=True
a.selectbox(key='galaxy').select('UGC01281').run();assert not a.exception
report['failed_baseline_does_not_crash']=True
a.selectbox(key='galaxy').select('NGC3198').run();a.toggle(key='lab_NGC3198_remove').set_value(True).run();assert not a.exception
assert any('INTERACTIVE PREVIEW' in w.value for w in a.warning)
next(b for b in a.button if b.label=='Restore original configuration').click().run();assert not a.toggle(key='lab_NGC3198_remove').value
report['remove_restore']=True
next(b for b in a.button if b.label=='Calculate preview').click().run();assert not a.exception
assert a.session_state['lab_NGC3198_preview']['label']=='INTERACTIVE PREVIEW'
report['parameter_preview']=True
for page in ['model_arena','fragility_atlas','evidence_vault','galaxy_lab']:
    a.switch_page('app_pages/'+page+'.py').run();assert not a.exception
report['four_modules']=True
# Controlled admission test, not a claim of forcing OS-wide memory pressure.
with patch('m4_ui.available',return_value=900):
    a.run();assert not a.exception
    assert next(b for b in a.button if b.label=='Run bounded exploratory fit').disabled
    assert any('Low memory' in w.value for w in a.warning)
report['simulated_900_MiB_low_memory_UI_refuses_fit']=True
report['actual_OS_memory_exhaustion_test']='Not performed; no unrelated applications stressed or terminated'
report['status']='PASS';report['seconds']=time.perf_counter()-start
(out/'ui_session_tests.json').write_bytes(json_bytes(report));print(json.dumps(report))
