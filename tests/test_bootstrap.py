"""Failure controls: synthetic control bytes are never benchmark observations."""
import hashlib,json
from pathlib import Path
import pytest
import benchmark_setup as b
def specimen(tmp_path,body=b'unit-control-only'):
    e={'url':'https://invalid.example/CONTROL.mrt','bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()};b.save(tmp_path/'data/manifests/acquisition.json',[e]);return e
def test_missing_benchmark_setup_state(tmp_path):assert b.state(tmp_path)[0] is False
def test_offline_before_setup(tmp_path):assert 'Setup required' in b.state(tmp_path)[1]
def test_download_failure(tmp_path):
    specimen(tmp_path)
    def fail(url):raise OSError('controlled network failure')
    with pytest.raises(OSError):b.acquire(tmp_path,fail)
    assert not list((tmp_path/'data/raw').glob('*.mrt'))
def test_unexpected_hash_not_saved(tmp_path):
    specimen(tmp_path)
    with pytest.raises(RuntimeError,match='source hash'):b.acquire(tmp_path,lambda u:(b'wrong bytes',200,u))
    assert not list((tmp_path/'data/raw').glob('*.mrt'))
def test_existing_corrupt_source_not_overwritten(tmp_path):
    e=specimen(tmp_path);p=tmp_path/'data/raw/CONTROL.mrt';p.parent.mkdir();p.write_bytes(b'bad')
    with pytest.raises(RuntimeError):b.acquire(tmp_path)
    assert p.read_bytes()==b'bad'
def test_incomplete_acquisition_no_completion(tmp_path):
    e=specimen(tmp_path);b.save(tmp_path/'data/manifests/acquisition.json',[e,{**e,'url':'https://invalid.example/SECOND.mrt'}])
    def partial(url):
        if 'SECOND' in url:raise OSError('controlled second-file failure')
        return b'unit-control-only',200,url
    with pytest.raises(OSError):b.acquire(tmp_path,partial)
    assert not b.read(tmp_path/'results/bootstrap/v1/acquisition.json')['complete']
def test_invalid_source_schema(tmp_path):
    p=tmp_path/'data/raw';p.mkdir(parents=True);(p/'SPARC_Lelli2016c.mrt').write_text('not a scientific table')
    with pytest.raises((ValueError,RuntimeError)):b.normalize(tmp_path)
def test_missing_manifest(tmp_path):
    b.save(tmp_path/'results/bootstrap/v1/receipt.json',{'schema':b.SCHEMA,'complete':True,'required_hashes':{},'manifest_hashes':{'m2':'missing'}})
    assert not b.state(tmp_path)[0]
def test_invalid_receipt_schema(tmp_path):
    b.save(tmp_path/'results/bootstrap/v1/receipt.json',{'schema':'incorrect','complete':True})
    assert 'Invalid' in b.state(tmp_path)[1]
def test_partial_checkpoint_refused(tmp_path):
    p=tmp_path/'checkpoint.json';b.save(p,{'bootstrap_identity':'id'})
    with pytest.raises(RuntimeError,match='checkpoint'):b.verify_checkpoint(tmp_path,p,{'revision':'id'})
def test_corrupt_checkpoint_refused(tmp_path):
    p=tmp_path/'checkpoint.json';b.save(p,{'bootstrap_identity':'id'});b.seal(p);p.write_text('{}')
    with pytest.raises(RuntimeError):b.verify_checkpoint(tmp_path,p,{'revision':'id'})
def test_wrong_source_checkpoint_refused(tmp_path):
    p=tmp_path/'checkpoint.json';b.save(p,{'bootstrap_identity':'old'});b.seal(p)
    with pytest.raises(RuntimeError,match='identity'):b.verify_checkpoint(tmp_path,p,{'revision':'new'})
