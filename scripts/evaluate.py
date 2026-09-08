"""Measure inferred alignment against sealed recipes, then transfer learned profiles."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from engine import learning, visual
from service import store
from service.main import execute, asset_audio

def main():
    recipes=json.loads((store.ROOT/'demo'/'ground-truth.json').read_text())
    errors=[]; accepted=0; good=0; results=[]
    current_raw={r['raw_id'] for r in recipes[:3]}
    for pair in [p for p in store.all('pair') if p['raw_id'] in current_raw]:
        execute({'task':'align','payload':{'pair_id':pair['id']}})
        pair=store.get(pair['id'],'pair')
        recipe=next(r for r in recipes[:3] if r['raw_id']==pair['raw_id'])
        name=store.get(pair['profile_id'])['name']
        reference=recipe['references'][name]['segments']
        for m in pair['alignment']['matches']:
            if m['status']!='proposed':continue
            # Accept only the algorithm's unique matches. Ground truth never changes acceptance.
            m['status']='accepted'; accepted+=1
            cursor=0;expected=None; midpoint=(m['final_start']+m['final_end'])/2
            for s in reference:
                if cursor<=midpoint<cursor+s['end']-s['start']:
                    expected=s['start']+m['final_start']-cursor;break
                cursor+=s['end']-s['start']
            error=abs(m['raw_start']-expected) if expected is not None else 999
            errors.append(error);good+=error<=.10
        pair['revision']+=1;store.save('pair',pair)
        execute({'task':'visual','payload':{'pair_id':pair['id']}})
        pair=store.get(pair['id'],'pair')
        for o in pair['visual']['observations']:
            if o['status']=='proposed':o['status']='accepted'
        pair['revision']+=1;store.save('pair',pair)
    versions={}
    for profile in store.all('profile'):
        pairs=[p for p in store.all('pair') if p['profile_id']==profile['id'] and p['raw_id'] in current_raw]
        for p in pairs:
            a=store.get(p['raw_id'],'asset');p.update(raw_regions=a['regions'],raw_words=a['words'])
        learned=learning.learn(pairs)
        learned['visual']=visual.learn(pairs)
        if learned['visual']['status']=='learned':
            learned['scope'].append('Centered visual framing')
            learned['unknown']=[u for u in learned['unknown'] if u!='Visual style']+['Graphics, color grade, crop timing']
        version=store.save('version',{**learned,'profile_id':profile['id'],'number':1+len([v for v in store.all('version') if v['profile_id']==profile['id']]),'pair_revisions':{p['id']:p['revision'] for p in pairs},'created':time.time()})
        versions[profile['name']]=version
        print(profile['name'],version['pause_seconds'],version['observation_count'],flush=True)
    for r in recipes[3:]:
        a=store.get(r['raw_id'],'asset')
        for name,version in versions.items():
            # Reference pause measured by the evaluator only, not passed to planning.
            refsegments=r['references'][name]['segments']
            from engine import media
            rawregions=media.speech_regions(asset_audio(a))
            target=float(np.median([s['end']-min(rawregions,key=lambda rg:abs(rg['start']-s['start']))['end'] for s in refsegments[:-1]]))
            personalized=learning.make_plan(a['regions'],a['duration'],version,a['words'])
            generic=learning.make_plan(a['regions'],a['duration'],None,a['words'])
            groups=learning.duplicate_groups(a['regions'],a['words'])
            take_correct=0;take_total=0
            for group in groups:
                for idx in group:
                    start=a['regions'][idx]['start']
                    predicted=any(abs(s['start']-start)<.08 for s in personalized['segments'])
                    expected=any(abs(s['start']-start)<.08 for s in refsegments)
                    take_correct+=predicted==expected;take_total+=1
            zoom_error=abs(personalized['visual']['zoom']-r['references'][name].get('visual_reference',{}).get('zoom',1))
            results.append({'session':r['session'],'split':r['split'],'profile':name,'personalized_error_ms':round(abs(personalized['pause_seconds']-target)*1000),'generic_error_ms':round(abs(.35-target)*1000),'take_agreement_pct':round(take_correct/max(1,take_total)*100,1),'take_decisions':take_total,'framing_zoom':personalized['visual']['zoom'],'framing_error':round(zoom_error,3)})
            for mode,plan in [('personalized',personalized),('generic',generic)]:
                if mode=='generic' and any(p['asset_id']==a['id'] and p['mode']=='generic' for p in store.all('plan')):continue
                saved=store.save('plan',{**plan,'asset_id':a['id'],'profile_version_id':version['id'] if mode=='personalized' else None,'revision':1,'history':[]})
                job=store.save('job',{'task':'export','payload':{'plan':saved},'status':'running','created':time.time(),'message':'Evaluation render'})
                result=execute(job);job.update(status='complete',result=result,message='Rendered and duration verified');store.save('job',job)
    evaluation={'status':'complete','training_sessions':3,'held_out_sessions':2,'alignment_matches':accepted,'alignment_precision_pct':round(good/max(accepted,1)*100,1),'correspondence_median_ms':round(float(np.median(errors))*1000,1),'correspondence_p95_ms':round(float(np.quantile(errors,.95))*1000,1),'results':results,'summary':'Measured transfer of pause spacing and repeated-take selection from three example sessions to two different tutorials. Audio correspondence is checked at the midpoint of each speech match, avoiding padded boundaries that cross a cut.','limitations':'Small engineered corpus with synthesized narration and simple cuts. The held-out sessions were used during integration debugging, so these are regression results, not a sealed final benchmark. Results establish mechanics, not real creator usefulness, broad visual style, or retention improvement.'}
    (store.ROOT/'demo'/'evaluation.json').write_text(json.dumps(evaluation,indent=2))
    print(json.dumps(evaluation,indent=2))

if __name__=='__main__':main()
