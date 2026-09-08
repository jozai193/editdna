"""Author constructed framing examples; the learner receives only rendered pixels."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import media
from service import store
from service.main import ingest
recipes=json.loads((store.ROOT/'demo'/'ground-truth.json').read_text())
for r in recipes:
    for name,reference in r['references'].items():
        zoom=1.10 if name=='Tight' else 1.0
        out=store.ROOT/'demo'/f'session-{r["session"]}-{name.lower()}-framing.mp4'
        media.render(store.ROOT/'assets'/r['raw_id'],reference['segments'],out,{'zoom':zoom})
        reference['visual_reference']={'zoom':zoom}
        if r['split']=='train':
            asset=ingest(out,f'{r["title"]} · {name.lower()} final.mp4','final')
            asset['provenance']='Owned synthetic tutorial: Windows speech and original slides';store.save('asset',asset)
            for p in store.all('pair'):
                if p['raw_id']==r['raw_id'] and store.get(p['profile_id'],'profile')['name']==name:
                    p.update(final_id=asset['id'],alignment=None,visual=None,revision=p['revision']+1,archived=False);store.save('pair',p)
            reference['asset_id']=asset['id']
        reference['file']=str(out)
    print('Rendered framing examples:',r['title'],flush=True)
(store.ROOT/'demo'/'ground-truth.json').write_text(json.dumps(recipes,indent=2))
