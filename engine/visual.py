"""Estimate centered reframing from corresponding raw/final frames.

This intentionally does not infer a whole aesthetic. It recovers a bounded,
observable crop transform and abstains when the frames do not correspond.
"""
import io
import numpy as np
from PIL import Image
from scipy.ndimage import sobel
from .media import run

def frame(path,seconds):
    raw=run(['ffmpeg','-v','error','-ss',max(0,seconds),'-i',path,'-frames:v','1','-vf','scale=480:-2','-f','image2pipe','-vcodec','png','-'])
    return Image.open(io.BytesIO(raw)).convert('RGB')

def crop(image,zoom):
    w,h=image.size;cw=round(w/zoom);ch=round(h/zoom)
    return image.crop(((w-cw)//2,(h-ch)//2,(w+cw)//2,(h+ch)//2)).resize((320,180),Image.Resampling.LANCZOS)

def descriptor(image):
    a=np.asarray(image.convert('L'),dtype=np.float32)/255
    edges=np.hypot(sobel(a,0),sobel(a,1))
    # Suppress compression noise and compare structural edges, not overall color.
    edges=np.maximum(edges-.025,0)
    return edges.ravel()

def estimate(raw,final):
    if abs(raw.width/raw.height-final.width/final.height)>.04:
        return {'status':'unresolved','reason':'Aspect ratios differ; centered crop model does not apply.'}
    target=descriptor(final.resize((320,180),Image.Resampling.LANCZOS));norm=np.linalg.norm(target)
    if norm<2:return {'status':'unresolved','reason':'Not enough visible detail to estimate framing.'}
    results=[]
    for zoom in np.arange(1,1.401,.005):
        vector=descriptor(crop(raw,float(zoom)))
        score=float(np.dot(target,vector)/max(norm*np.linalg.norm(vector),1e-8))
        results.append((score,float(zoom)))
    score,zoom=max(results)
    competitor=max(s for s,z in results if abs(z-zoom)>=.04)
    if score<.80 or score-competitor<.06:
        return {'status':'unresolved','reason':'Frames do not support a unique centered crop.','score':round(score,4)}
    return {'status':'proposed','zoom':round(zoom,3),'score':round(score,4),'margin':round(score-competitor,4)}

def analyze_pair(raw_path,final_path,matches):
    candidates=[m for m in matches if m['status']=='accepted']
    if not candidates:return {'observations':[],'method':'centered-crop-v1'}
    # Samples span the edit. Observations in the same raw session count as one session.
    selected=np.linspace(0,len(candidates)-1,min(5,len(candidates)),dtype=int)
    observations=[]
    for idx in selected:
        m=candidates[int(idx)];rt=(m['raw_start']+m['raw_end'])/2;ft=(m['final_start']+m['final_end'])/2
        result=estimate(frame(raw_path,rt),frame(final_path,ft))
        observations.append({**result,'match_id':m['id'],'raw_time':round(rt,3),'final_time':round(ft,3)})
    return {'observations':observations,'method':'centered-crop-v1'}

def learn(pairs):
    session_values={};evidence=[]
    for p in pairs:
        for o in (p.get('visual') or {}).get('observations',[]):
            if o['status']!='accepted':continue
            session_values.setdefault(p['raw_id'],[]).append(o['zoom'])
            evidence.append({**o,'pair_id':p['id'],'raw_id':p['raw_id']})
    values=[float(np.median(v)) for v in session_values.values()]
    if len(values)<3:return {'status':'unknown','session_count':len(values),'evidence':evidence,'reason':'Accept consistent visual matches from at least three independent sources.'}
    spread=float(np.std(values));zoom=float(np.median(values))
    if spread>.035:return {'status':'unknown','session_count':len(values),'evidence':evidence,'reason':'Example framing is inconsistent. No fixed crop is applied.'}
    return {'status':'learned','zoom':round(zoom,3),'session_count':len(values),'spread':round(spread,4),'evidence':evidence,'scope':'Centered framing only','warnings':['Check faces, text, and edge content before export.','This does not learn graphics, color grading, camera movement, or crop timing.']}
