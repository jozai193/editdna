"""Create a read-only hosted demonstration from real local pipeline artifacts."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service import store
from service.main import state,execute,captions

def main():
    recipes=json.loads((store.ROOT/'demo'/'ground-truth.json').read_text())
    asset_ids={r['raw_id'] for r in recipes}
    asset_ids.update(ref['asset_id'] for r in recipes[:3] for ref in r['references'].values())
    pairs=[p for p in store.all('pair') if p['raw_id'] in asset_ids and p['final_id'] in asset_ids]
    pair_ids={p['id'] for p in pairs}
    versions=[]
    for profile in store.all('profile'):
        latest=next((v for v in store.all('version') if v['profile_id']==profile['id'] and set(v['pair_revisions']).issubset(pair_ids)),None)
        if latest:versions.append(latest)
    version_ids={v['id'] for v in versions}
    plans=[];seen=set()
    for p in store.all('plan'):
        if p.get('trial_id'):continue
        if p['asset_id'] not in asset_ids:continue
        if p['profile_version_id'] and p['profile_version_id'] not in version_ids:continue
        key=(p['asset_id'],p['profile_version_id'])
        if key not in seen:plans.append(p);seen.add(key)
    plan_ids={p['id'] for p in plans}; exports=[]
    for p in plans:
        # Re-render every shipped plan with the final engine, including generic baseline.
        id=store.new_id();job=store.save('job',{'id':id,'task':'export','payload':{'plan':p},'status':'running','message':'Preparing demo export'})
        result=execute(job);job.update(status='complete',result=result,message='Video and bundle verified');store.save('job',job);exports.append(result)
    export_ids={e['id'] for e in exports}
    # Keep prototypes on disk for reproducibility, but archive them from the workspace.
    for kind,ids in [('pair',pair_ids),('version',version_ids),('plan',plan_ids),('export',export_ids),('job',export_ids)]:
        for item in store.all(kind):
            if item.get('trial_id') or (kind=='export' and store.get(item['plan_id'],'plan').get('trial_id')):continue
            item['archived']=item['id'] not in ids;store.save(kind,item)
    for a in store.all('asset'):
        if 'Owned synthetic' in a.get('provenance',''):
            a['archived']=a['id'] not in asset_ids;store.save('asset',a)
    output=Path(__file__).resolve().parents[1]/'web'/'public'/'demo';output.mkdir(parents=True,exist_ok=True)
    (output/'media').mkdir(exist_ok=True);(output/'exports').mkdir(exist_ok=True)
    snapshot=state()
    # Hosted data is an explicit allowlist of owned fixtures, never a user's library.
    snapshot['assets']=[a for a in snapshot['assets'] if a['id'] in asset_ids]
    snapshot['pairs']=pairs
    snapshot['versions']=versions
    snapshot['profiles']=[p for p in snapshot['profiles'] if p['id'] in {v['profile_id'] for v in versions}]
    snapshot['plans']=plans
    snapshot['exports']=exports
    snapshot['jobs']=[j for j in snapshot['jobs'] if j['id'] in export_ids]
    # Strip internal job payloads from the hosted snapshot.
    snapshot['jobs']=[{k:v for k,v in j.items() if k not in ('payload','result')} for j in snapshot['jobs']]
    for a in snapshot['assets']:
        shutil.copyfile(store.ROOT/'assets'/a['id'],output/'media'/(a['id']+'.mp4'))
        _,vtt=captions(a.get('words',[]),[{'start':0,'end':a['duration']}])
        (output/'media'/(a['id']+'.vtt')).write_text(vtt,encoding='utf8')
    for e in snapshot['exports']:shutil.copytree(store.ROOT/'exports'/e['id'],output/'exports'/e['id'],dirs_exist_ok=True)
    (output/'trial-tasks.json').write_text(json.dumps(recipes[3:]),encoding='utf8')
    (output/'state.json').write_text(json.dumps(snapshot),encoding='utf8')
    shutil.copyfile(store.ROOT/'demo'/'evaluation.json',output/'evaluation.json')
    print('Packaged',len(snapshot['assets']),'assets,',len(snapshot['plans']),'plans,',len(snapshot['exports']),'exports')

if __name__=='__main__':main()
