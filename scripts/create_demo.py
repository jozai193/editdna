"""Owned, synthesized tutorial corpus. Recipes stay outside the learner inputs."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont
from engine import media
from service import store
from service.main import ingest

FOLDER=store.ROOT/'demo'; FOLDER.mkdir(exist_ok=True)
TOPICS=[
 ('Build a clear thumbnail',['Start with one clear subject.','Place your subject on the left.','Use three words in the headline.','Do not use thirty words.','Choose a contrasting background.','Check the thumbnail at small size.','Keep the same visual language.','Export your finished thumbnail.']),
 ('Record cleaner audio',['Move your microphone closer.','Keep the input below clipping.','Record ten seconds of room tone.','Do not remove every breath.','Listen for background noise.','Turn off the loud ceiling fan.','Check your headphones before recording.','Save a copy of the original.']),
 ('Organize a filming day',['Write the lesson in one sentence.','List the shots you need.','Charge two camera batteries.','Do not format the backup card.','Record a short sound check.','Leave room for another take.','Label every source folder.','Back up the entire session.']),
 ('Light a small studio',['Place your key light at an angle.','Turn off the overhead lamp.','Keep the light two feet away.','Do not point it into your eyes.','Add a white reflector beside you.','Check the shadows on your face.','Lock the exposure before recording.','Save this lighting setup.']),
 ('Publish an accessible tutorial',['Start with a descriptive title.','Explain each action out loud.','Use at least sixteen point text.','Do not rely on color alone.','Check every generated caption.','Include the essential keyboard shortcuts.','Review the video without audio.','Publish the accessible version.'])]

def make():
    manifest=[]
    for i,(title,lines) in enumerate(TOPICS):
        for j,text in enumerate(lines):manifest.append({'path':str(FOLDER/f'voice-{i}-{j}.wav'),'text':text})
        for j in (1,5):manifest.append({'path':str(FOLDER/f'retake-{i}-{j}.wav'),'text':lines[j],'rate':-1})
    path=FOLDER/'speech.json';path.write_text(json.dumps(manifest),encoding='utf8')
    media.run(['powershell','-NoProfile','-File',Path(__file__).with_name('make_speech.ps1'),'-Manifest',path])
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',42); small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',23)
    records=[]
    for i,(title,lines) in enumerate(TOPICS):
        source=FOLDER/f'session-{i+1}.mp4'; pieces=[]; timing=[];cursor=0
        clips=[]
        for j,line in enumerate(lines):
            clips.append((j,line,'voice'))
            if j in (1,5):clips.append((j,line,'retake'))
        for position,(j,line,take) in enumerate(clips):
            voice=media.audio(FOLDER/f'{take}-{i}-{j}.wav',FOLDER/f'{take}16-{i}-{j}.wav')
            regions=media.speech_regions(voice)
            voice=voice[int(regions[0]['start']*media.RATE):int(regions[-1]['end']*media.RATE)]
            gap=.9+(j%3)*.25
            timing.append({'start':cursor,'end':cursor+len(voice)/media.RATE,'text':line,'group':j,'take':take})
            pieces.extend([voice,np.zeros(int(gap*media.RATE),dtype=np.float32)])
            cursor+=len(voice)/media.RATE+gap
        wavfile.write(FOLDER/f'raw-{i}.wav',media.RATE,(np.concatenate(pieces)*32767).astype(np.int16))
        im=Image.new('RGB',(1280,720),'#101721');d=ImageDraw.Draw(im)
        d.text((75,58),'EDITDNA  /  OWNED DEMONSTRATION',font=small,fill='#9bdacb')
        d.text((75,120),title,font=font,fill='#ffffff')
        for j,line in enumerate(lines):d.text((80,215+j*50),f'{j+1:02}   {line}',font=small,fill='#c8d2e2')
        d.text((75,665),f'Session {i+1}  ·  Synthesized narration  ·  Constructed editing preferences',font=small,fill='#8192a8')
        image=FOLDER/f'slide-{i}.png';im.save(image)
        media.run(['ffmpeg','-v','error','-y','-loop','1','-i',image,'-i',FOLDER/f'raw-{i}.wav','-c:v','libx264','-tune','stillimage','-r','24','-pix_fmt','yuv420p','-c:a','aac','-shortest',source])
        raw=ingest(source,f'{title} · raw.mp4');raw['provenance']='Owned synthetic tutorial: Windows speech and original slides';store.save('asset',raw)
        record={'session':i+1,'title':title,'raw_id':raw['id'],'split':'train' if i<3 else 'validation' if i==3 else 'test','references':{}}
        for name,gap in [('Tight',.12),('Deliberate',.62)]:
            selected=[s for s in timing if s['group'] not in (1,5) or s['take']==('retake' if name=='Tight' else 'voice')]
            segments=[{'start':s['start'],'end':s['end']+(gap if n<len(selected)-1 else 0)} for n,s in enumerate(selected)]
            final=FOLDER/f'session-{i+1}-{name.lower()}.mp4';media.render(source,segments,final)
            record['references'][name]={'file':str(final),'segments':segments}
            if i<3:
                asset=ingest(final,f'{title} · {name.lower()} final.mp4','final')
                asset['provenance']=raw['provenance'];store.save('asset',asset)
                record['references'][name]['asset_id']=asset['id']
        records.append(record)
        print('Created',title,flush=True)
    # Reference maps are evaluation-only. Backend learner receives media, never this file.
    (FOLDER/'ground-truth.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    profiles={p['name']:p for p in store.all('profile')}
    for name in ('Tight','Deliberate'):
        profile=profiles.get(name) or store.save('profile',{'name':name})
        for r in records[:3]:
            existing=next((p for p in store.all('pair') if p['profile_id']==profile['id'] and p['raw_id']==r['raw_id']),None)
            if existing:
                if existing['final_id']!=r['references'][name]['asset_id']:
                    existing.update(final_id=r['references'][name]['asset_id'],alignment=None,revision=existing['revision']+1)
                    store.save('pair',existing)
            else:
                store.save('pair',{'profile_id':profile['id'],'raw_id':r['raw_id'],'final_id':r['references'][name]['asset_id'],'name':r['title'],'revision':1,'alignment':None,'provenance':'Constructed demonstration'})
    print('Five source sessions and ten reference edits ready.',flush=True)

if __name__=='__main__':make()
