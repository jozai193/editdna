"""Audio alignment and conservative preference extraction, independent of demo recipes."""
import re
import numpy as np
from scipy.signal import correlate, resample_poly
from .media import RATE, speech_regions

def align(raw, final):
    # Match speech, not silence. Use 8 kHz waveform correlation and normalized scores.
    r=resample_poly(raw,1,2).astype(np.float64); sr=RATE//2
    cumulative=np.r_[0,np.cumsum(r*r)]
    result=[]
    for index,region in enumerate(speech_regions(final,min_silence=.10)):
        a,b=region['start'],region['end']
        q=resample_poly(final[int(a*RATE):int(b*RATE)],1,2).astype(np.float64)
        if len(q)>len(r) or len(q)<sr*.12: continue
        corr=correlate(r,q,mode='valid',method='fft')
        energy=cumulative[len(q):]-cumulative[:-len(q)]
        scores=corr/np.sqrt(np.maximum(energy*np.sum(q*q),1e-14))
        best=int(np.argmax(scores)); score=float(scores[best])
        alternatives=[]
        work=scores.copy()
        for _ in range(3):
            p=int(np.argmax(work)); val=float(work[p])
            if val < max(.55,score-.08): break
            alternatives.append({'start':round(p/sr,4),'score':round(val,4)})
            work[max(0,p-int(.2*sr)):min(len(work),p+int(.2*sr))]=-1
        ambiguous=len(alternatives)>1
        result.append({'id':f'm{index}', 'final_start':a,'final_end':b,'raw_start':best/sr,'raw_end':best/sr+b-a,'score':round(score,4),'alternatives':alternatives,'status':'proposed' if score>=.72 and not ambiguous else 'unresolved'})
    # Unique strong matches act as anchors for ambiguous repeated audio.
    # Never silently resolve equal-quality repeated takes.
    coverage=sum(m['final_end']-m['final_start'] for m in result if m['status']=='proposed')/(len(final)/RATE)
    return {'matches':result,'coverage':round(coverage,4),'method':'normalized-waveform-v1','warnings':['Music, time stretching, and changed narration can require manual alignment.']}

def learn(pairs):
    values=[]; evidence=[]; sessions=set(); take_evidence=[]
    for pair in pairs:
        matches=sorted([m for m in pair['alignment']['matches'] if m['status']=='accepted'],key=lambda m:m['final_start'])
        per_pair=[]
        for left,right in zip(matches,matches[1:]):
            rawgap=right['raw_start']-left['raw_end']
            finalgap=right['final_start']-left['final_end']
            if .45 <= rawgap <= 4 and 0 <= finalgap <= min(rawgap-.12,2):
                per_pair.append(finalgap)
                evidence.append({'pair_id':pair['id'],'left_match':left['id'],'right_match':right['id'],'raw_pause':round(rawgap,3),'kept_pause':round(finalgap,3)})
        if per_pair:
            values.append(float(np.median(per_pair))); sessions.add(pair['raw_id'])
        regions=pair.get('raw_regions',[])
        for group in duplicate_groups(regions,pair.get('raw_words',[])):
            coverage=[]
            for idx in group:
                r=regions[idx]
                covered=sum(max(0,min(r['end'],m['raw_end'])-max(r['start'],m['raw_start'])) for m in matches)
                coverage.append(min(1,covered/(r['end']-r['start'])))
            selected=[n for n,c in enumerate(coverage) if c>.65]
            if len(selected)==1 and all(c<.15 for n,c in enumerate(coverage) if n!=selected[0]):
                take_evidence.append({'pair_id':pair['id'],'raw_id':pair['raw_id'],'group':group,'selected':group[selected[0]],'preference':'first' if selected[0]==0 else 'last'})
    if not values: raise ValueError('Accept consecutive, reliable matches in at least one example before learning.')
    observed=float(np.median(values)); support=len(sessions)
    weight=min(1,support/3)
    target=observed*weight+.35*(1-weight)
    take_sessions={e['raw_id'] for e in take_evidence}
    first=sum(e['preference']=='first' for e in take_evidence)
    consistency=max(first,len(take_evidence)-first)/max(1,len(take_evidence))
    preference=('first' if first>len(take_evidence)/2 else 'last') if len(take_sessions)>=3 and consistency>=.8 else None
    return {'pause_seconds':round(target,3),'observed_pause_seconds':round(observed,3),'session_count':support,'observation_count':len(evidence),'spread_seconds':round(float(np.std(values)),3),'origin':'learned','confidence':'supported' if support>=3 else 'limited','evidence':evidence,'take_preference':preference,'take_evidence':take_evidence,'algorithm':'session-balanced-median-v2','scope':['Pause spacing']+(['Repeated take selection'] if preference else []),'unknown':['Visual style','Narrative restructuring','Audience retention']+([] if preference else ['Take preferences'])}

def normalized(text):
    return ' '.join(re.findall(r"[a-z0-9']+",text.lower()))

def region_texts(regions,words):
    texts=[[] for _ in regions]
    for w in words:
        overlaps=[max(0,min(w['end'],r['end'])-max(w['start'],r['start'])) for r in regions]
        if overlaps and max(overlaps)>0:texts[int(np.argmax(overlaps))].append(w['word'])
        elif w['start']==w['end']:
            # Whisper occasionally emits a zero-duration token inside speech.
            index=next((i for i,r in enumerate(regions) if r['start']<=w['start']<=r['end']),None)
            if index is not None:texts[index].append(w['word'])
    return [' '.join(t) for t in texts]

def duplicate_groups(regions,words):
    texts=region_texts(regions,words);groups=[];i=0
    while i<len(regions)-1:
        a=normalized(texts[i]);b=normalized(texts[i+1])
        # Exact multiword equivalence only; numbers and negations are not discarded.
        if len(a.split())>=4 and a==b and regions[i+1]['start']-regions[i]['end']<3:
            group=[i,i+1];j=i+2
            while j<len(regions) and normalized(texts[j])==a and regions[j]['start']-regions[j-1]['end']<3:
                group.append(j);j+=1
            groups.append(group);i=j
        else:i+=1
    return groups

def signature(text):
    return re.findall(r"\b(?:\d+(?:\.\d+)?|no|not|never|without|must|cannot|can't)\b",text.lower())

def make_plan(regions,duration,profile=None,words=None):
    target=profile['pause_seconds'] if profile else .35
    segments=[]; decisions=[]; removed=set();take_preference=profile.get('take_preference') if profile else None
    if take_preference:
        for group in duplicate_groups(regions,words or []):
            selected=group[0] if take_preference=='first' else group[-1]
            for idx in group:
                if idx==selected:continue
                removed.add(idx)
                decisions.append({'id':f't{idx}','kind':'take','start':regions[idx]['start'],'end':regions[idx]['end'],'removed':round(regions[idx]['end']-regions[idx]['start'],3),'reason':f'Keep the {take_preference} of equivalent repeated takes.','origin':'learned','evidence_count':len(profile.get('take_evidence',[]))})
    kept=[i for i in range(len(regions)) if i not in removed]
    texts=region_texts(regions,words or [])
    for pos,i in enumerate(kept):
        r=regions[i]
        start=max(0,r['start']); end=min(duration,r['end'])
        if pos<len(kept)-1:
            next_index=kept[pos+1]
            gap=max(0,regions[next_index]['start']-end)
            # Never extend through a rejected take while preserving a pause.
            available=max(0,regions[i+1]['start']-end) if i+1<len(regions) else gap
            keep=min(gap,target,available)
            end+=keep
            if gap-keep>.02:
                decisions.append({'id':f'd{i}','kind':'pause','start':r['end'],'end':regions[next_index]['start'],'removed':round(gap-keep,3),'reason':f'Keep {keep:.2f}s between phrases.','origin':'learned' if profile else 'default','evidence_count':len(profile.get('evidence',[])) if profile else 0})
        segments.append({'id':f's{i}','start':round(start,4),'end':round(end,4),'text':texts[i]})
    if not segments: raise ValueError('No speech detected. Try a clearer recording or adjust the speech threshold.')
    visual=(profile or {}).get('visual',{})
    framing={'zoom':visual['zoom'],'origin':'learned','session_count':visual['session_count']} if visual.get('status')=='learned' else {'zoom':1,'origin':'default'}
    return {'segments':segments,'decisions':decisions,'duration':round(sum(s['end']-s['start'] for s in segments),3),'source_duration':duration,'pause_seconds':target,'take_preference':take_preference,'visual':framing,'mode':'personalized' if profile else 'generic','warnings':['Repeated takes are removed only for exact transcript equivalence and a supported learned preference. Review all cuts.']}
