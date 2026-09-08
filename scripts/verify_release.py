"""Exercise the local HTTP workflow in an isolated, restored demo workspace."""
import os
import sys
import time
import json
import uuid
from pathlib import Path
project=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(project))
os.environ['EDITDNA_DATA']=str(project/'data'/'release-checks'/uuid.uuid4().hex)
from scripts.restore_demo import main as restore
from service.main import app
from service import store
from fastapi.testclient import TestClient

restore()
with TestClient(app) as client:
    state=client.get('/api/v1/state').json()
    source=next(a for a in state['assets'] if 'accessible' in a['name'])
    with (store.ROOT/'assets'/source['id']).open('rb') as media:
        response=client.post('/api/v1/assets',files={'file':('owned-demo.mp4',media,'video/mp4')})
    assert response.status_code==200 and response.json()['id']==source['id'],response.text
    version=state['versions'][0]
    response=client.post('/api/v1/plans',json={'asset_id':source['id'],'profile_version_id':version['id']})
    assert response.status_code==200,response.text
    plan=response.json();assert len(plan['segments'])==8
    segments=plan['segments'];segments[0]['locked']=True
    response=client.patch('/api/v1/plans/'+plan['id'],json={'segments':segments},headers={'If-Match':'1'})
    assert response.status_code==200,response.text
    response=client.post('/api/v1/plans/'+plan['id']+'/undo',headers={'If-Match':'2'})
    assert response.status_code==200,response.text
    job=client.post('/api/v1/plans/'+plan['id']+'/export').json()
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        current=store.get(job['id'],'job')
        if current['status'] in ('complete','failed'):break
        time.sleep(.2)
    assert current['status']=='complete',current
    checks={}
    for file in ('edit.mp4','captions.srt','captions.vtt','edit-plan.json','manifest.json','editdna-export.zip'):
        r=client.get(f'/api/v1/exports/{job["id"]}/{file}')
        assert r.status_code==200 and len(r.content)>0,(file,r.status_code)
        checks[file]=len(r.content)
    r=client.get('/api/v1/assets/'+source['id']+'/captions.vtt');assert r.status_code==200 and r.text.startswith('WEBVTT')
    r=client.get('/api/v1/assets/'+source['id']+'/media',headers={'range':'bytes=0-99'});assert r.status_code==206 and len(r.content)==100
    result={'status':'passed','steps':['restore demo','upload real media','HTTP create personalized plan','lock segment','undo revision','background render','download six artifacts','source captions','video range request'],'download_bytes':checks}
    (project/'data'/'release-verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
