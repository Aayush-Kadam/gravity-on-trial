"""Controlled stop/restart + final preview/browser visual checks; leaves no server."""
import json,os,subprocess,sys,time,urllib.request
import psutil
from playwright.sync_api import sync_playwright
from m4_adapter import *
from m4_browser_tests import verify_curve,screenshot,choose,nav,settle,REPORT
OUT=ROOT/'results/m4/v1'
def main():
    old=[]
    for p in psutil.process_iter(['name','cmdline']):
        cmd=p.info['cmdline'] or []
        if p.info['name']=='python.exe' and 'run' in cmd and any(a==str(ROOT/'streamlit_app.py') for a in cmd):
            old.append(p.pid);p.terminate();p.wait(timeout=10)
    time.sleep(.5)
    # Prior measurement is frozen before supervisor writes a new run.
    prior=OUT/'server_monitor.json'
    if prior.exists():(OUT/'full_browser_server_monitor.json').write_bytes(prior.read_bytes())
    server=subprocess.Popen([sys.executable,str(ROOT/'m4_serve.py'),'streamlit_app.py','8507'],env=os.environ,cwd=ROOT)
    started=time.perf_counter();pid=None
    try:
        for _ in range(100):
            if server.poll() is not None:raise RuntimeError('Restart refused/failed; inspect preflight and logs')
            try:
                if urllib.request.urlopen('http://127.0.0.1:8507/_stcore/health',timeout=.5).read()==b'ok':break
            except Exception:time.sleep(.1)
        else:raise TimeoutError('Restart health timeout')
        pid=json.loads((OUT/'server_pid.json').read_text())['pid']
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True,args=['--disable-gpu'])
            context=browser.new_context(viewport={'width':1366,'height':768},service_workers='block')
            blocked=[]
            def route(r):
                if r.request.url.startswith('http://127.0.0.1:8507/'):r.continue_()
                else:blocked.append(r.request.url);r.abort()
            context.route('**/*',route);page=context.new_page();page.goto('http://127.0.0.1:8507');page.get_by_role('heading',name='NGC3198',exact=True).wait_for(timeout=25000)
            b=read(baseline_path('NGC3198'));restart=verify_curve(page,b)
            screenshot(page,'final_laptop_galaxy_lab')
            page.get_by_text('Explore parameters · explicit preview or bounded fit',exact=True).click()
            field=page.get_by_role('spinbutton',name='Disk mass-to-light ratio (solar, 3.6 μm)',exact=True);field.fill('0.55');field.press('Tab');page.get_by_role('button',name='Calculate preview',exact=True).click()
            page.get_by_text('INTERACTIVE PREVIEW · parameters changed',exact=False).wait_for()
            expected=preview(b,'nfw',{'ud':.55,'ub':.7,'d':1.,'inc':73.})
            verify_curve(page,b,MODELS+['preview'],preview_record=expected)
            page.get_by_role('button',name='Restore original configuration',exact=True).click();verify_curve(page,b)
            for module in ['Model arena','Fragility atlas','Evidence vault','Galaxy lab']:
                nav(page,module);assert not page.locator('[data-testid="stException"]').count()
            settle(page);screenshot(page,'final_galaxy_lab_top')
            page.locator('.js-plotly-plot').first.screenshot(path=str(OUT/'final_rotation_residuals.png'))
            nav(page,'Fragility atlas');settle(page);screenshot(page,'final_atlas_laptop')
            page.get_by_text('Galaxy detail',exact=True).click();settle(page);screenshot(page,'final_atlas_detail_laptop')
            browser.close()
        report={'status':'PASS','old_task_server_pids':old,'restart_source_baseline_sha256':fingerprint(baseline_path('NGC3198')),'restart_actual_DOM_arrays':restart,'parameter_preview_browser_values_verified':True,'restore_after_preview':True,'final_four_module_navigation':True,'all_nonlocal_origins_blocked':True,'blocked_requests':blocked,'viewport':'1366x768','seconds':time.perf_counter()-started,'compatible_starlette':__import__('starlette').__version__}
        (OUT/'restart_and_preview_browser.json').write_bytes(json_bytes(report));print(json.dumps(report))
    finally:
        if pid:
            try:psutil.Process(pid).terminate()
            except psutil.NoSuchProcess:pass
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.terminate();server.wait(timeout=5)
if __name__=='__main__':main()
