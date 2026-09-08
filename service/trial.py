"""A controlled human editing pilot. No synthetic time-saving results."""
import json
import time
from . import store
from engine import learning

def start():
    recipe_file=store.ROOT/'demo'/'ground-truth.json'
    recipes=json.loads(recipe_file.read_text())[3:] if recipe_file.exists() else json.loads((store.ROOT/'demo'/'trial-tasks.json').read_text())
    profile=next(p for p in store.all('profile') if p['name']=='Tight')
    version=next(v for v in store.all('version') if v['profile_id']==profile['id'] and v.get('visual',{}).get('status')=='learned')
    # Alternating order across participants; this is descriptive, not a randomized study.
    order=['manual','assisted'] if len(store.all('trial'))%2==0 else ['assisted','manual']
    return store.save('trial',{'revision':1,'created_at':time.time(),'order':order,'version_id':version['id'],'tasks':[{'condition':condition,'asset_id':recipes[i]['raw_id'],'title':recipes[i]['title'],'reference':recipes[i]['references']['Tight']['segments']} for i,condition in enumerate(order)],'runs':[],'status':'ready'})

def begin(id):
    trial=store.get(id,'trial')
    if trial['status']=='running':raise ValueError('Finish the current task first.')
    index=len(trial['runs'])
    if index>=2:raise ValueError('Both tasks are complete.')
    task=trial['tasks'][index];asset=store.get(task['asset_id'],'asset');started=time.time()
    if task['condition']=='assisted':
        result=learning.make_plan(asset['regions'],asset['duration'],store.get(trial['version_id'],'version'),asset['words'])
    else:
        texts=learning.region_texts(asset['regions'],asset['words'])
        segments=[{'id':f's{i}','start':r['start'],'end':asset['regions'][i+1]['start'] if i+1<len(asset['regions']) else asset['duration'],'text':texts[i]} for i,r in enumerate(asset['regions'])]
        result={'segments':segments,'duration':sum(s['end']-s['start'] for s in segments),'source_duration':asset['duration'],'visual':{'zoom':1,'origin':'manual'},'decisions':[],'mode':'manual'}
    plan=store.save('plan',{**result,'asset_id':asset['id'],'profile_version_id':trial['version_id'] if task['condition']=='assisted' else None,'revision':1,'history':[],'trial_id':id})
    return store.revise('trial',id,trial['revision'],{'status':'running','active':{'plan_id':plan['id'],'started_at':started,'condition':task['condition'],'title':task['title']}})

def finish(id,reviewed):
    trial=store.get(id,'trial')
    if trial['status']!='running':raise ValueError('Start a task first.')
    if not reviewed:raise ValueError('Watch the full rendered edit and confirm its quality first.')
    active=trial['active'];plan=store.get(active['plan_id'],'plan')
    exported=next((e for e in store.all('export') if e['plan_id']==plan['id'] and e['revision']==plan['revision']),None)
    if not exported:raise ValueError('Render your current revision before finishing.')
    reference=trial['tasks'][len(trial['runs'])]['reference'];segments=plan['segments']
    if len(segments)!=len(reference):raise ValueError('Keep eight instructions, removing the earlier copy of each repeated take.')
    if any(abs(s['start']-r['start'])>.18 or abs(s['end']-r['end'])>.18 for s,r in zip(segments,reference)):
        raise ValueError('Check speech boundaries and trailing pauses: retain all speech and about 0.12 seconds after each phrase.')
    if abs((plan.get('visual') or {}).get('zoom',1)-1.1)>.01:raise ValueError('Set centered framing to 1.10 times.')
    runs=trial['runs']+[{**active,'finished_at':time.time(),'elapsed_seconds':round(time.time()-active['started_at'],2),'plan_revision':plan['revision'],'export_id':exported['id'],'quality_check':'passed','playback_confirmed_by_user':True}]
    changes={'runs':runs,'status':'complete' if len(runs)==2 else 'ready'}
    if len(runs)==2:
        times={r['condition']:r['elapsed_seconds'] for r in runs}
        changes['result']={'manual_seconds':times['manual'],'assisted_seconds':times['assisted'],'saved_seconds':round(times['manual']-times['assisted'],2),'saved_percent':round(100*(times['manual']-times['assisted'])/times['manual'],1),'limitation':'One participant, two different constructed tutorials, preloaded transcripts and trained profile. Includes review and rendering; excludes onboarding and training. Prior exposure and task order can affect results. No claim about typical creators.'}
    return store.revise('trial',id,trial['revision'],changes)
