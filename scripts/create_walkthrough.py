"""Narrated walkthrough from real browser screenshots and a real rendered export."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import media
root=Path(__file__).resolve().parents[1];out=root/'docs'/'submission';work=root/'data'/'walkthrough';work.mkdir(exist_ok=True)
parts=[
 ('studio','Creators repeat the same small editing decisions on every recording. Edit DNA learns those decisions from your own finished edits. This walkthrough uses actual application captures, owned synthetic tutorials, and synthesized narration. The working editor produces real video, captions, and an inspectable edit plan.'),
 ('examples','Pair a raw recording with its finished edit. Edit DNA finds corresponding speech, and lets you review the match before learning. It also compares corresponding visual frames. The visual model learns fixed centered framing, such as this one point one times crop. It does not claim to learn graphics or color grading.'),
 ('profile','Preferences require evidence across independent source sessions. These examples teach two contrasting profiles: deliberate pauses and first takes, or tighter pauses and later equivalent takes. A profile version preserves what was learned. Every resulting cut can be restored, adjusted, locked, or undone.'),
 ('evaluation','The engine transfers these preferences to two different tutorials. Our constructed regression set recovers all fifty accepted audio matches and all sixteen take decisions. Pause targets are closer to the reference than the generic preset. The two framing preferences also transfer. These are small synthetic regression results, not a sealed benchmark or a claim about typical creators.'),
 ('timed-trial','To measure usefulness, the local app prepares a timed human editing pilot. Manual and assisted conditions use the same quality target. The clock includes editing, rendering, and playback review. Results are recorded only after the participant completes both tasks. No human time saving is invented. Here is an actual rendered output from Edit DNA.')]
manifest=[{'path':str(work/f'voice-{i}.wav'),'text':text} for i,(_,text) in enumerate(parts)]
(work/'speech.json').write_text(json.dumps(manifest),encoding='utf8')
media.run(['powershell','-NoProfile','-File',root/'scripts'/'make_speech.ps1','-Manifest',work/'speech.json'])
clips=[]
for i,(name,_) in enumerate(parts):
 clip=work/f'part-{i}.mp4';media.run(['ffmpeg','-v','error','-y','-loop','1','-i',out/f'{name}.png','-i',work/f'voice-{i}.wav','-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2','-r','30','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-shortest',clip]);clips.append(clip)
state=json.loads((root/'web'/'public'/'demo'/'state.json').read_text())
plan=next(p for p in state['plans'] if p.get('visual',{}).get('zoom')==1.1)
export=next(e for e in state['exports'] if e['plan_id']==plan['id'])
clip=work/'output.mp4';media.run(['ffmpeg','-v','error','-y','-i',root/'web'/'public'/'demo'/'exports'/export['id']/'edit.mp4','-vf','scale=1280:720','-r','30','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2',clip]);clips.append(clip)
listing=work/'clips.txt';listing.write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips))
media.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',out/'editdna-demo.mp4'])
print(media.probe(out/'editdna-demo.mp4'))
