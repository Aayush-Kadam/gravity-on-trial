"""Real Edge browser workflows. Start m4_serve.py first; no external services."""
import csv,io,json,sys,time,traceback
from pathlib import Path
import numpy as np
import psutil
from r0_processes import usage
from playwright.sync_api import sync_playwright
from m4_adapter import *
OUT=ROOT/'results/m4/v1';REPORT={'browser':'Microsoft Edge headless / Playwright 1.56','workflows':{},'screenshots':[],'external_requests_blocked':[],'timings':{},'fatal_browser_errors':[]}
def record(name,fn):
    start=time.perf_counter();value=fn();REPORT['workflows'][name]={'status':'PASS','seconds':time.perf_counter()-start,'detail':value};(OUT/'browser_workflows.json').write_bytes(json_bytes(REPORT))
def settle(page):
    page.wait_for_timeout(180)
    page.locator('.js-plotly-plot').first.wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('.js-plotly-plot')?.data?.length > 0",timeout=20000)
    assert not page.locator('[data-testid="stException"]').count()
def choose(page,label,value):
    box=page.get_by_role('combobox',name=label,exact=True);box.click();box.fill(value)
    page.wait_for_timeout(180)
    option=page.get_by_role('option',name=value,exact=True)
    if option.count():option.click()
    else:box.press('ArrowDown');box.press('Enter')
    page.wait_for_timeout(250)
def nav(page,name):
    page.locator('[data-testid="stSidebarNav"] a').filter(has_text=name).click();page.wait_for_timeout(250)
def traces(page):return page.locator('.js-plotly-plot').first.evaluate('(x)=>x.data.map(t=>({name:t.name,y:Array.from(t.y||[]),x:Array.from(t.x||[]),error:Array.from(t.error_y?.array||[])}))')
def verify_curve(page,b,model_names=MODELS,mode='MLE',preview_record=None):
    settle(page);data=traces(page)
    np.testing.assert_array_equal(data[0]['y'],b['observed_km_s']);np.testing.assert_array_equal(data[0]['error'],b['error_km_s']);np.testing.assert_array_equal(data[0]['x'],b['radius_kpc'])
    for name in model_names:
        r=result(b,name,mode) if name!='preview' else preview_record;label=LABELS.get(name,name)
        found=[t for t in data if t['name']==label]
        if 'prediction_km_s' not in r:assert not found;continue
        assert len(found)==2
        np.testing.assert_array_equal(found[0]['y'],r['prediction_km_s'])
        np.testing.assert_allclose(found[1]['y'],(np.array(r['prediction_km_s'])-b['observed_km_s'])/b['error_km_s'],rtol=1e-13,atol=1e-13)
    return {'galaxy':b['galaxy'],'observations':len(b['radius_kpc']),'models':model_names,'actual_DOM_arrays_verified':True}
def screenshot(page,name):
    page.evaluate("document.querySelector('[data-testid=stMain]').scrollTo(0,0)");page.wait_for_timeout(200);page.screenshot(path=str(OUT/(name+'.png')));REPORT['screenshots'].append(name+'.png')
def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True,args=['--disable-gpu'])
        context=browser.new_context(viewport={'width':1440,'height':900},service_workers='block',accept_downloads=True)
        def route(r):
            url=r.request.url
            if url.startswith(('http://127.0.0.1:8507/','ws://127.0.0.1:8507/','data:','blob:')):r.continue_()
            else:REPORT['external_requests_blocked'].append(url);r.abort()
        context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:REPORT['fatal_browser_errors'].append(str(e)))
        start=time.perf_counter();page.goto('http://127.0.0.1:8507');page.get_by_role('heading',name='NGC3198',exact=True).wait_for(timeout=30000);settle(page);REPORT['timings']['first_render_seconds']=time.perf_counter()-start
        b=read(baseline_path('NGC3198'));record('01_startup',lambda:verify_curve(page,b));screenshot(page,'galaxy_lab_desktop')
        def switching():
            start=time.perf_counter();choose(page,'Galaxy · 175 SPARC objects','NGC2403');page.get_by_role('heading',name='NGC2403',exact=True).wait_for();v=verify_curve(page,read(baseline_path('NGC2403')));REPORT['timings']['galaxy_switch_seconds']=time.perf_counter()-start
            choose(page,'Galaxy · 175 SPARC objects','NGC3198');verify_curve(page,b);return v
        record('02_galaxy_selection',switching)
        def toggles():
            for m in MODELS:
                page.get_by_role('button',name=LABELS[m],exact=True).click();settle(page);data=traces(page);assert not any(t['name']==LABELS[m] for t in data)
                page.get_by_role('button',name=LABELS[m],exact=True).click();verify_curve(page,b)
            return 'All four model toggles verified against actual Plotly traces'
        record('03_model_toggle',toggles)
        def remove():
            page.get_by_text('Remove dark matter',exact=True).click();page.get_by_text('INTERACTIVE PREVIEW · halo removed',exact=False).wait_for();v=verify_curve(page,b,['preview'],preview_record=remove_halo(b,result(b,'nfw')))
            page.get_by_role('button',name='Restore original configuration').click();verify_curve(page,b);return v
        record('04_remove_and_restore',remove);record('05_residuals',lambda:verify_curve(page,b))
        def statistics():
            nav(page,'Model arena');choose(page,'Galaxy · 175 SPARC objects','CamB');settle(page);page.get_by_text('Unavailable ·',exact=False).first.wait_for();assert not page.get_by_text('Operationally preferred:',exact=False).count()
            choose(page,'Galaxy · 175 SPARC objects','NGC3198');settle(page);page.get_by_text('MAP',exact=True).click();settle(page);verify_curve(page,b,mode='MAP');page.get_by_text('MAP penalties are not ordinary likelihood evidence',exact=False).wait_for();screenshot(page,'model_arena_MAP');return 'Unavailable CamB; MAP unranked; actual MAP arrays verified'
        record('06_statistical_validity',statistics)
        def ident():
            page.get_by_text('Identifiability warning',exact=False).wait_for();return 'Explicit MAP identifiability warning visible'
        record('07_identifiability',ident)
        def atlas():
            nav(page,'Fragility atlas');settle(page);assert page.locator('[data-testid="stMetricValue"]').all_text_contents()==['79','18','5','5']
            metrics=read('results/m3/v1/atlas_metrics.json');examples={k:next(m['galaxy'] for m in metrics if m['classification']==k and m['baseline_status']=='PREFERENCE') for k in ['STABLE','SENSITIVE','INCONCLUSIVE','UNASSESSABLE']}
            screenshot(page,'atlas_population')
            choose(page,'Drill into an aggregate galaxy',examples['SENSITIVE']);page.get_by_role('button',name='Open galaxy detail').click();page.get_by_role('heading',name=examples['SENSITIVE']+' · SENSITIVE',exact=True).wait_for();settle(page)
            for k,g in examples.items():
                choose(page,'Galaxy · 175 SPARC objects',g);page.get_by_role('heading',name=g+' · '+k,exact=True).wait_for();settle(page)
            screenshot(page,'atlas_galaxy_detail');return examples
        record('08_atlas_classes_and_drilldown',atlas)
        def invalid():
            # Exact failed/unsupported cases chosen from saved records, never fabricated.
            found={}
            for g in catalog():
                s=read(scenario_path(g))
                for sc in s['scenarios']:
                    for r in sc['results']:
                        if r['status'] in ['UNSUPPORTED_DOMAIN','NO_VALID_START','INVALID_PROPOSAL'] and r['status'] not in found:found[r['status']]=(g,sc['scenario_id'])
                if len(found)==3:break
            for status,(g,sid) in found.items():
                choose(page,'Galaxy · 175 SPARC objects',g);settle(page);choose(page,'Perturbation scenario',sid);settle(page);page.locator('[data-testid="stAlert"]').filter(has_text=status).first.wait_for()
                source=next(sc for sc in read(scenario_path(g))['scenarios'] if sc['scenario_id']==sid)
                bad=[r for r in source['results'] if r['status']!='CONVERGED'];data=traces(page)
                assert all(not any(t['name']==LABELS[r['model']] for t in data) for r in bad)
            return found
        record('09_failed_unsupported_invalid',invalid)
        def exports():
            nav(page,'Evidence vault');choose(page,'Galaxy · 175 SPARC objects','NGC3198');page.get_by_role('button',name='Download curve CSV').wait_for()
            with page.expect_download() as dl:page.get_by_role('button',name='Download curve CSV').click()
            dest=OUT/'browser_download.csv';dl.value.save_as(str(dest));rows=list(csv.DictReader(io.StringIO(dest.read_text())))
            assert len(rows)==43;np.testing.assert_array_equal([float(r['nfw_MLE_prediction_km_s']) for r in rows],result(b,'nfw')['prediction_km_s']);np.testing.assert_array_equal([float(r['observed_km_s']) for r in rows],b['observed_km_s'])
            with page.expect_download() as dl:page.get_by_role('button',name='Download original galaxy record').click()
            dest=OUT/'browser_download.json';dl.value.save_as(str(dest));assert json.loads(dest.read_text())==b;screenshot(page,'evidence_vault');return 'CSV and JSON downloaded in browser and matched source'
        record('10_evidence_downloads',exports)
        pid=json.loads((OUT/'server_pid.json').read_text())['pid'];proc=psutil.Process(pid);rss=[]
        def navigation():
            for i in range(4):
                for name in ['Galaxy lab','Model arena','Fragility atlas','Evidence vault']:
                    nav(page,name);page.wait_for_timeout(350);assert not page.locator('[data-testid="stException"]').count()
                rss.append(usage(proc)[0])
            REPORT['navigation_rss_MiB']=rss;return {'cycles':4,'module_visits':16,'RSS_after_cycles_MiB':rss,'growth_last_minus_first_MiB':rss[-1]-rss[0]}
        record('11_navigation',navigation)
        def offline():
            # All external origins have been blocked since startup; local app origin remains reachable.
            nav(page,'Galaxy lab');verify_curve(page,b);nav(page,'Fragility atlas');settle(page);return 'Core workflows passed with all non-local origins blocked; installation/setup already complete'
        record('13_offline_core',offline)
        nav(page,'Galaxy lab');page.set_viewport_size({'width':1366,'height':768});settle(page);screenshot(page,'galaxy_lab_laptop');page.get_by_role('combobox',name='Galaxy · 175 SPARC objects').focus();assert page.get_by_role('combobox',name='Galaxy · 175 SPARC objects').evaluate('(x)=>document.activeElement===x')
        REPORT['keyboard_focus']='Galaxy combobox keyboard-focusable';REPORT['status']='PASS' if not REPORT['fatal_browser_errors'] else 'FAIL';(OUT/'browser_workflows.json').write_bytes(json_bytes(REPORT));print(json.dumps(REPORT));browser.close()
if __name__=='__main__':
    try:main()
    except Exception as e:
        REPORT['status']='FAIL';REPORT['failure']=traceback.format_exc();(OUT/'browser_workflows.json').write_bytes(json_bytes(REPORT));raise
