import json
import os
import shutil
import threading
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from engine import media, learning, visual
from . import store
from . import trial

ROOT=store.ROOT
ALLOWED=['http://localhost:3000','http://127.0.0.1:3000','http://localhost:5173','http://127.0.0.1:5173','http://127.0.0.1:8765']
stop=threading.Event()

def asset_audio(asset): return media.audio(ROOT/'assets'/asset['id'], ROOT/'audio'/(asset['id']+'.wav'))

def ingest(path,name,role='raw'):
    info=media.probe(path)
    id=media.digest(path)
    try:
        existing=store.get(id,'asset')
        return existing
    except KeyError:pass
    target=ROOT/'assets'/id
    if not target.exists(): shutil.copyfile(path,target)
    samples=media.audio(target,ROOT/'audio'/(id+'.wav'))
    return store.save('asset',{'id':id,'name':Path(name).name,'role':role,'duration':info['duration'],'video':info['video'],'peaks':media.peaks(samples),'regions':media.speech_regions(samples),'words':[],'transcript_status':'not_requested'})

def captions(words,segments):
    mapped=[]; offset=0
    for s in segments:
        for w in words:
            a=max(w['start'],s['start']); b=min(w['end'],s['end'])
            if a<b: mapped.append({'start':offset+a-s['start'],'end':offset+b-s['start'],'word':w['word']})
        offset+=s['end']-s['start']
    def stamp(t,comma=False):
        ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02}{"," if comma else "."}{ms:03}'
    cues=[mapped[i:i+7] for i in range(0,len(mapped),7)]
    srt='\n\n'.join(f'{i+1}\n{stamp(c[0]["start"],True)} --> {stamp(c[-1]["end"],True)}\n'+ ' '.join(w['word'] for w in c) for i,c in enumerate(cues))
    vtt='WEBVTT\n\n'+'\n\n'.join(f'{stamp(c[0]["start"])} --> {stamp(c[-1]["end"])}\n'+' '.join(w['word'] for w in c) for c in cues)
    return srt,vtt

def execute(job):
    p=job['payload']; kind=job['task']
    if kind=='align':
        pair=store.get(p['pair_id'],'pair'); raw=store.get(pair['raw_id'],'asset'); final=store.get(pair['final_id'],'asset')
        result=learning.align(asset_audio(raw),asset_audio(final))
        pair.update(alignment=result,visual=None,revision=pair.get('revision',1)+1)
        store.save('pair',pair); return {'pair_id':pair['id']}
    if kind=='visual':
        pair=store.get(p['pair_id'],'pair')
        if not pair.get('alignment'):raise ValueError('Analyze and accept audio matches first.')
        result=visual.analyze_pair(ROOT/'assets'/pair['raw_id'],ROOT/'assets'/pair['final_id'],pair['alignment']['matches'])
        return store.revise('pair',pair['id'],pair['revision'],{'visual':result})
    if kind=='transcribe':
        from faster_whisper import WhisperModel
        asset=store.get(p['asset_id'],'asset')
        model=WhisperModel(os.environ.get('EDITDNA_ASR_MODEL','base.en'),device='cpu',compute_type='int8',download_root=str(ROOT/'models'))
        segments,_=model.transcribe(str(ROOT/'assets'/asset['id']),word_timestamps=True,language='en',vad_filter=True)
        asset['words']=[{'start':w.start,'end':w.end,'word':w.word.strip()} for s in segments for w in (s.words or [])]
        asset['transcript_status']='complete';store.save('asset',asset);return {'asset_id':asset['id']}
    if kind=='export':
        plan=p['plan']; asset=store.get(plan['asset_id'],'asset')
        folder=ROOT/'exports'/job['id'];folder.mkdir(exist_ok=True)
        partial=folder/'render.partial.mp4'; media.render(ROOT/'assets'/asset['id'],plan['segments'],partial,plan.get('visual'))
        partial.replace(folder/'edit.mp4')
        srt,vtt=captions(asset.get('words',[]),plan['segments'])
        (folder/'captions.srt').write_text(srt,encoding='utf8');(folder/'captions.vtt').write_text(vtt,encoding='utf8')
        (folder/'edit-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf8')
        manifest={'source_sha256':asset['id'],'profile_version_id':plan.get('profile_version_id'),'plan_id':plan['id'],'revision':plan['revision'],'video_sha256':media.digest(folder/'edit.mp4'),'caption_words':len(asset.get('words',[])),'engine':'editdna-0.1','provenance':asset.get('provenance','User supplied recording')}
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        with zipfile.ZipFile(folder/'editdna-export.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in folder.iterdir():
                if f.suffix!='.zip': z.write(f,f.name)
        result={'id':job['id'],'plan_id':plan['id'],'revision':plan['revision'],'duration':plan['duration'],'created':time.time(),'has_captions':bool(asset.get('words'))}
        store.save('export',result);return result
    raise ValueError('Unknown job type')

def worker():
    # This local edition runs one worker. Pending jobs persist across server restarts.
    for j in store.all('job'):
        if j['status']=='running' and not j.get('archived'): j.update(status='queued',message='Resuming after restart');store.save('job',j)
    while not stop.is_set():
        jobs=[j for j in reversed(store.all('job')) if j['status']=='queued' and not j.get('archived')]
        if not jobs: stop.wait(.5);continue
        job=jobs[0];job.update(status='running',started=time.time());store.save('job',job)
        try:
            result=execute(job);job.update(status='complete',result=result,message='Complete')
        except Exception as e:
            job.update(status='failed',message=str(e)[-1600:])
        job['finished']=time.time();store.save('job',job)

@asynccontextmanager
async def lifespan(app):
    stop.clear();t=threading.Thread(target=worker,daemon=True);t.start()
    yield
    stop.set()

app=FastAPI(title='EditDNA local engine',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED,allow_methods=['GET','POST','PATCH'],allow_headers=['Content-Type','If-Match'])

@app.middleware('http')
async def local_boundary(request:Request,call_next):
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin not in ALLOWED:return JSONResponse({'detail':'Untrusted application origin'},status_code=403)
    if request.headers.get('host','').split(':')[0] not in ('127.0.0.1','localhost','testserver'):
        return JSONResponse({'detail':'This engine is local only.'},status_code=403)
    try: return await call_next(request)
    except KeyError:return JSONResponse({'detail':'Item not found'},status_code=404)
    except ValueError as e:return JSONResponse({'detail':str(e)},status_code=400)

def enqueue(task,payload):
    existing=next((j for j in store.all('job') if j['task']==task and j['payload']==payload and j['status'] in ('queued','running')),None)
    if existing:return existing
    return store.save('job',{'task':task,'payload':payload,'status':'queued','message':'Waiting for the local engine','created':time.time()})

@app.post('/api/v1/jobs/{id}/cancel')
def cancel_job(id:str):
    job=store.get(id,'job')
    if job['status']!='queued':raise HTTPException(409,'Only waiting jobs can be cancelled. Active media processing must finish.')
    job.update(status='cancelled',message='Cancelled before processing');return store.save('job',job)

@app.get('/api/v1/state')
def state():
    result={k:store.all(kind) for k,kind in [('assets','asset'),('profiles','profile'),('pairs','pair'),('versions','version'),('plans','plan'),('jobs','job'),('exports','export')]}
    return {k:[v for v in values if not v.get('archived')] for k,values in result.items()}

@app.get('/api/v1/health')
def health():return {'status':'ok','engine':'local','version':'0.1.0'}

@app.post('/api/v1/assets')
async def upload(file:UploadFile=File(...)):
    path=ROOT/'assets'/(store.new_id()+'.upload');size=0
    try:
        with path.open('wb') as f:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>2*1024**3:raise HTTPException(413,'Maximum file size is 2 GB.')
                f.write(chunk)
        return ingest(path,file.filename or 'Recording')
    finally:
        path.unlink(missing_ok=True)

@app.get('/api/v1/assets/{id}/media')
def asset_file(id:str):
    a=store.get(id,'asset');return FileResponse(ROOT/'assets'/a['id'],media_type='video/mp4' if a['video'] else 'audio/wav')

@app.get('/api/v1/assets/{id}/captions.vtt')
def asset_captions(id:str):
    a=store.get(id,'asset')
    _,vtt=captions(a.get('words',[]),[{'start':0,'end':a['duration']}])
    return Response(vtt,media_type='text/vtt')

@app.get('/api/v1/assets/{id}/frame')
def frame_file(id:str,t:float=0):
    import math
    a=store.get(id,'asset')
    if not a['video'] or not math.isfinite(t) or not 0<=t<a['duration']:raise HTTPException(400,'Choose a valid video timestamp.')
    target=ROOT/'audio'/f'{id}-{round(t,2):.2f}.jpg'
    if not target.exists():visual.frame(ROOT/'assets'/id,t).save(target,quality=90)
    return FileResponse(target,media_type='image/jpeg')

@app.post('/api/v1/assets/{id}/transcribe')
def transcribe(id:str):
    store.get(id,'asset');return enqueue('transcribe',{'asset_id':id})

class ProfileInput(BaseModel): name:str=Field(min_length=1,max_length=100)
@app.post('/api/v1/profiles')
def create_profile(body:ProfileInput):return store.save('profile',{'name':body.name})

class PairInput(BaseModel):
    profile_id:str; raw_id:str; final_id:str; name:str=Field(max_length=150,default='Example edit')
@app.post('/api/v1/pairs')
def create_pair(body:PairInput):
    store.get(body.profile_id,'profile');store.get(body.raw_id,'asset');store.get(body.final_id,'asset')
    if body.raw_id==body.final_id:raise ValueError('Choose different raw and final recordings.')
    return store.save('pair',{**body.model_dump(),'revision':1,'alignment':None})

@app.post('/api/v1/pairs/{id}/analyze')
def analyze(id:str):store.get(id,'pair');return enqueue('align',{'pair_id':id})

@app.post('/api/v1/pairs/{id}/visual')
def analyze_visual(id:str):store.get(id,'pair');return enqueue('visual',{'pair_id':id})

@app.patch('/api/v1/pairs/{id}/visual')
async def review_visual(id:str,request:Request):
    version=request.headers.get('if-match')
    if not version:raise HTTPException(428,'Reload before saving.')
    pair=store.get(id,'pair');body=await request.json();result=pair.get('visual')
    if not result:raise ValueError('Analyze visual matches first.')
    for observation in result['observations']:
        update=next((o for o in body['observations'] if o['match_id']==observation['match_id']),None)
        if not update:continue
        if update['status'] not in ('accepted','rejected','proposed'):raise ValueError('Invalid review status.')
        if observation['status']=='unresolved' and update['status']=='accepted':raise ValueError('Unresolved visual matches cannot be accepted.')
        observation['status']=update['status']
    try:return store.revise('pair',id,int(version),{'visual':result})
    except ValueError as e:raise HTTPException(409,str(e))

@app.patch('/api/v1/pairs/{id}/alignment')
async def update_alignment(id:str,request:Request):
    version=request.headers.get('if-match')
    if not version:raise HTTPException(428,'Reload the example before saving.')
    body=await request.json();pair=store.get(id,'pair');alignment=pair['alignment']
    if not alignment:raise ValueError('Analyze this pair first.')
    updates={m['id']:m for m in body['matches']}
    duration=store.get(pair['raw_id'],'asset')['duration']
    for m in alignment['matches']:
        if m['id'] not in updates:continue
        u=updates[m['id']]
        if u['status'] not in ('accepted','rejected','unresolved','proposed'):raise ValueError('Invalid match status')
        a=float(u.get('raw_start',m['raw_start']));b=a+m['final_end']-m['final_start']
        if not 0<=a<b<=duration+.02:raise ValueError('Match outside source bounds')
        m.update(status=u['status'],raw_start=a,raw_end=b)
    try:return store.revise('pair',id,int(version),{'alignment':alignment})
    except ValueError as e:raise HTTPException(409,str(e))

@app.post('/api/v1/profiles/{id}/learn')
def learn_profile(id:str):
    store.get(id,'profile');pairs=[p for p in store.all('pair') if p['profile_id']==id and p['alignment'] and not p.get('archived')]
    for p in pairs:
        a=store.get(p['raw_id'],'asset');p.update(raw_regions=a['regions'],raw_words=a['words'])
    profile=learning.learn(pairs)
    profile['visual']=visual.learn(pairs)
    if profile['visual']['status']=='learned':
        profile['scope'].append('Centered visual framing')
        profile['unknown']=[u for u in profile['unknown'] if u!='Visual style']+['Graphics, color grade, and crop timing']
    return store.save('version',{**profile,'profile_id':id,'number':1+len([v for v in store.all('version') if v['profile_id']==id]),'pair_revisions':{p['id']:p['revision'] for p in pairs},'created':time.time()})

class PlanInput(BaseModel): asset_id:str; profile_version_id:str|None=None
class SegmentInput(BaseModel):
    id:str=Field(default='',max_length=100)
    start:float=Field(ge=0,allow_inf_nan=False)
    end:float=Field(gt=0,allow_inf_nan=False)
    text:str=Field(default='',max_length=5000)
    locked:bool=False
class VisualInput(BaseModel):zoom:float=Field(ge=1,le=1.4,allow_inf_nan=False)
class PlanPatch(BaseModel):
    segments:list[SegmentInput]=Field(min_length=1,max_length=300)
    visual:VisualInput|None=None
@app.post('/api/v1/plans')
def plan(body:PlanInput):
    asset=store.get(body.asset_id,'asset');profile=store.get(body.profile_version_id,'version') if body.profile_version_id else None
    result=learning.make_plan(asset['regions'],asset['duration'],profile,asset['words'])
    return store.save('plan',{**result,**body.model_dump(),'revision':1,'history':[]})

@app.patch('/api/v1/plans/{id}')
async def edit_plan(id:str,request:Request):
    version=request.headers.get('if-match')
    if not version:raise HTTPException(428,'Reload the plan before saving.')
    plan=store.get(id,'plan');body=PlanPatch.model_validate(await request.json());segments=[s.model_dump() for s in body.segments]
    if not 1<=len(segments)<=300:raise ValueError('Keep between 1 and 300 segments.')
    last=0
    for s in segments:
        if not 0<=float(s['start'])<float(s['end'])<=plan['source_duration'] or s['start']<last:raise ValueError('Segments must be in source order and inside the recording.')
        last=s['end']
    for old in plan['segments']:
        if old.get('locked'):
            changed=next((s for s in segments if s['id']==old['id']),None)
            if not changed or (changed.get('locked') and (changed['start']!=old['start'] or changed['end']!=old['end'])):
                raise ValueError('Unlock this segment before changing its boundaries or removing it.')
    changes={'segments':segments,'duration':sum(s['end']-s['start'] for s in segments),'history':(plan['history']+[plan['segments']])[-20:],'visual_history':(plan.get('visual_history',[plan.get('visual')]*len(plan['history']))+[plan.get('visual')])[-20:]}
    if body.visual:changes['visual']={**body.visual.model_dump(),'origin':'user_set'}
    try:return store.revise('plan',id,int(version),changes)
    except ValueError as e:raise HTTPException(409,str(e))

@app.post('/api/v1/plans/{id}/export')
def export(id:str):return enqueue('export',{'plan':store.get(id,'plan')})

@app.post('/api/v1/plans/{id}/undo')
async def undo_plan(id:str,request:Request):
    version=request.headers.get('if-match')
    if not version:raise HTTPException(428,'Reload the plan before saving.')
    plan=store.get(id,'plan')
    if not plan['history']:raise ValueError('No earlier edit remains.')
    segments=plan['history'][-1]
    try:return store.revise('plan',id,int(version),{'segments':segments,'duration':sum(s['end']-s['start'] for s in segments),'history':plan['history'][:-1],'visual':plan.get('visual_history',[plan.get('visual')])[-1],'visual_history':plan.get('visual_history',[])[:-1]})
    except ValueError as e:raise HTTPException(409,str(e))

@app.get('/api/v1/exports/{id}/{filename}')
def download(id:str,filename:str):
    store.get(id,'export')
    if filename not in ('edit.mp4','editdna-export.zip','edit-plan.json','captions.srt','captions.vtt','manifest.json'):raise HTTPException(404)
    return FileResponse(ROOT/'exports'/id/filename,filename=filename)

@app.get('/api/v1/evaluation')
def evaluation():
    file=ROOT/'demo'/'evaluation.json'
    return json.loads(file.read_text()) if file.exists() else {'status':'not_run','message':'Run the evaluation script to measure the engine.'}

@app.post('/api/v1/trials')
def create_trial():return trial.start()

@app.get('/api/v1/trials/{id}')
def get_trial(id:str):return store.get(id,'trial')

@app.post('/api/v1/trials/{id}/begin')
def begin_trial(id:str):return trial.begin(id)

class TrialFinish(BaseModel):reviewed:bool=False
@app.post('/api/v1/trials/{id}/finish')
def finish_trial(id:str,body:TrialFinish):return trial.finish(id,body.reviewed)
