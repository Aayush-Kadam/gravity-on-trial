"""M4 scientific presentation and boundary tests; complements the 92 regressions."""
import copy,csv,io,json
import numpy as np
import pytest
from m4_adapter import *
from m4_fit import admitted
def test_vertical():assert validate_vertical()['observations_unchanged']
def test_catalog():assert len(catalog())==175 and len(set(catalog()))==175
def test_path_guard():
    with pytest.raises(ValueError):baseline_path('../README')
def test_changed_input_rejected():
    with pytest.raises(ValueError):checked_read(baseline_path('NGC3198'),'wronghash')
@pytest.mark.parametrize('mode',['MLE','MAP'])
def test_remove_preserves_nuisance(mode):
    b=read(baseline_path('NGC3198'));before=json_bytes(b);r=result(b,'nfw',mode);removed=remove_halo(b,r)
    np.testing.assert_array_equal(removed['prediction_km_s'],predict(curve(b),'baryons',[],**assumptions(b,r)))
    assert before==json_bytes(b)
def test_map_unranked():
    b=read(baseline_path('NGC3198'));rs,c=scientific_state(b,'MAP');assert c['winner'] is None
    assert all(r['AIC'] is None and r['AICc'] is None and r['BIC'] is None for r in score_rows(rs))
def test_invalid_preview_rejected():
    b=read(baseline_path('NGC3198'))
    with pytest.raises(DomainError):preview(b,'baryons',{'ud':.5,'ub':.7,'d':0,'inc':73})
def test_scenario_assumptions():
    b=read(baseline_path('NGC3198'));s=read(scenario_path('NGC3198'))['scenarios'][0]
    for r in s['results']:assert assumptions(b,r)['ud']==s['spec']['upsilon_disk']
@pytest.mark.parametrize('heads,expected',[([900]*5,False),([1200,1400,1200,1200,1200],False),([1500]*5,True)])
def test_memory_admission(heads,expected):assert admitted(heads)==expected
def test_exports_preserve_all_radii():
    b=read(baseline_path('NGC3198'));r=result(b,'nfw');rows=list(csv.DictReader(io.StringIO(csv_bytes(table(b,{'nfw':r})).decode())))
    np.testing.assert_array_equal([float(x['observed_km_s']) for x in rows],b['observed_km_s'])
def test_undefined_comparison_retained():
    b=read(baseline_path('CamB'));rs,c=scientific_state(b);assert c['winner'] is None and c['status']=='NO_VALID_COMPARISON'
def test_signed_component():
    b=read(baseline_path('NGC3198'));c=curve(b);assert np.any(c.gas<0)
    np.testing.assert_array_equal(signed_baryons(c.gas,c.disk,c.bulge),.5*c.disk**2+.7*c.bulge**2+c.gas*np.abs(c.gas))
