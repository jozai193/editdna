import os
import tempfile
os.environ['EDITDNA_DATA']=tempfile.mkdtemp(prefix='editdna-test-')
from fastapi.testclient import TestClient
from service.main import app, captions, enqueue
from service import store

def test_cross_origin_mutations_rejected():
    client=TestClient(app)
    assert client.post('/api/v1/profiles',json={'name':'Test'},headers={'origin':'https://untrusted.example'}).status_code==403
    assert client.get('/api/v1/health',headers={'host':'untrusted.example'}).status_code==403

def test_unknown_record_and_nonmedia_upload():
    client=TestClient(app)
    assert client.get('/api/v1/assets/missing/media').status_code==404
    assert client.post('/api/v1/assets',files={'file':('fake.mp4',b'not a movie','video/mp4')}).status_code==400

def test_plan_revision_conflict_and_source_bounds():
    p=store.save('plan',{'revision':1,'source_duration':10,'segments':[{'start':0,'end':5}],'history':[]})
    c=TestClient(app);url=f'/api/v1/plans/{p["id"]}'
    assert c.patch(url,json={'segments':[{'start':0,'end':4}]}).status_code==428
    assert c.patch(url,json={'segments':[{'start':0,'end':11}]},headers={'If-Match':'1'}).status_code==400
    assert c.patch(url,json={'segments':[{'start':0,'end':4}]},headers={'If-Match':'1'}).status_code==200
    assert c.patch(url,json={'segments':[{'start':0,'end':3}]},headers={'If-Match':'1'}).status_code==409

def test_caption_remapping_removes_cut_words():
    srt,vtt=captions([{'word':'kept','start':2,'end':2.5},{'word':'removed','start':5,'end':6}],[{'start':2,'end':3}])
    assert '00:00:00,000 --> 00:00:00,500' in srt
    assert 'removed' not in srt and vtt.startswith('WEBVTT')

def test_duplicate_pending_job_reused():
    a=enqueue('align',{'pair_id':'test'});b=enqueue('align',{'pair_id':'test'})
    assert a['id']==b['id']

def test_visual_edit_undo_restores_previous_framing():
    p=store.save('plan',{'revision':1,'source_duration':10,'segments':[{'id':'s','start':0,'end':5}],'history':[],'visual':{'zoom':1.1,'origin':'learned'}})
    c=TestClient(app);url=f'/api/v1/plans/{p["id"]}'
    changed=c.patch(url,json={'segments':p['segments'],'visual':{'zoom':1.2}},headers={'If-Match':'1'})
    assert changed.status_code==200
    undo=c.post(url+'/undo',headers={'If-Match':'2'})
    assert undo.json()['visual']==p['visual']

def test_trial_requires_render_review_and_quality_before_time_claim():
    from service import trial
    import time
    p=store.save('plan',{'revision':1,'segments':[{'start':0,'end':1}],'visual':{'zoom':1.1}})
    t=store.save('trial',{'revision':1,'status':'running','active':{'plan_id':p['id'],'started_at':time.time(),'condition':'manual'},'runs':[],'tasks':[{'reference':[{'start':0,'end':1}]}]})
    import pytest
    with pytest.raises(ValueError,match='Watch'):trial.finish(t['id'],False)
    with pytest.raises(ValueError,match='Render'):trial.finish(t['id'],True)
    store.save('export',{'plan_id':p['id'],'revision':1})
    completed=trial.finish(t['id'],True)
    assert completed['runs'][0]['elapsed_seconds']>=0
    assert 'result' not in completed

def test_job_and_export_can_share_identifier():
    store.save('job',{'id':'shared','status':'complete'})
    store.save('export',{'id':'shared','duration':2})
    assert store.get('shared','job')['status']=='complete'
    assert store.get('shared','export')['duration']==2

def test_undo_consumes_history_and_locked_segments_require_unlock():
    p=store.save('plan',{'revision':1,'source_duration':10,'segments':[{'id':'s','start':0,'end':5,'locked':True}],'history':[]})
    c=TestClient(app);url=f'/api/v1/plans/{p["id"]}'
    assert c.patch(url,json={'segments':[{'id':'s','start':0,'end':4,'locked':True}]},headers={'If-Match':'1'}).status_code==400
    assert c.patch(url,json={'segments':[{'id':'s','start':0,'end':4,'locked':False}]},headers={'If-Match':'1'}).status_code==200
    result=c.post(url+'/undo',headers={'If-Match':'2'})
    assert result.status_code==200
    assert result.json()['segments'][0]['end']==5
    assert result.json()['history']==[]
