"""Deterministic media operations; all subprocess arguments are locally compiled."""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile

RATE = 16000

def run(args, timeout=600):
    p = subprocess.run([str(a) for a in args], capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors='replace')[-1800:])
    return p.stdout

def probe(path):
    with open(path,'rb') as f: head=f.read(64)
    supported=(head[4:8]==b'ftyp' or head.startswith((b'RIFF',b'\x1aE\xdf\xa3',b'OggS',b'fLaC',b'ID3')) or head[:2] in (b'\xff\xfb',b'\xff\xf3',b'\xff\xf2'))
    if not supported:raise ValueError('Unsupported media. Use MP4, MOV, WebM, WAV, MP3, Ogg, or FLAC.')
    info = json.loads(run(['ffprobe', '-v', 'error', '-protocol_whitelist','file,pipe','-show_format', '-show_streams', '-of', 'json', path]))
    if not any(s['codec_type'] == 'audio' for s in info['streams']):
        raise ValueError('This recording needs an audio track.')
    duration = float(info['format']['duration'])
    if not 0 < duration <= 1200:
        raise ValueError('Recordings must be between 0 and 20 minutes.')
    return {'duration': duration, 'video': any(s['codec_type']=='video' for s in info['streams']), 'streams': info['streams']}

def audio(path, cache):
    cache = Path(cache)
    if not cache.exists():
        run(['ffmpeg','-v','error','-y','-protocol_whitelist','file,pipe','-i',path,'-vn','-ac','1','-ar',RATE,'-c:a','pcm_s16le',cache])
    rate, samples = wavfile.read(cache)
    return samples.astype(np.float32) / 32768

def speech_regions(samples, threshold_db=-38, min_silence=.22, padding=.045):
    step = int(RATE*.02)
    n = len(samples)//step
    if not n: return []
    rms = np.sqrt(np.mean(samples[:n*step].reshape(n,step)**2,axis=1))
    # Relative gate handles quieter recordings, with a floor against numerical noise.
    gate = max(10**(threshold_db/20), float(np.quantile(rms,.9))*.045)
    active = np.flatnonzero(rms > gate)
    if not len(active): return []
    groups = np.split(active, np.where(np.diff(active)*.02 > min_silence)[0]+1)
    return [{'start':max(0,float(g[0]*.02-padding)), 'end':min(len(samples)/RATE,float((g[-1]+1)*.02+padding))} for g in groups if len(g)*.02 >= .10]

def peaks(samples, count=360):
    return [round(float(np.max(np.abs(c))),4) for c in np.array_split(samples,min(count,len(samples))) if len(c)]

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def render(source, segments, output, visual=None):
    info=probe(source)
    if not segments: raise ValueError('The edit must keep at least one segment.')
    if len(segments)>300: raise ValueError('Maximum 300 edit segments.')
    filters=[]; audio_inputs=[]
    for i,s in enumerate(segments):
        a,b=float(s['start']),float(s['end'])
        if not 0 <= a < b <= info['duration']+.015: raise ValueError('Edit boundaries exceed the source.')
        fade=min(.008,(b-a)/4)
        filters.append(f'[0:a]atrim=start={a:.6f}:end={b:.6f},asetpts=N/SR/TB,apad=whole_dur={b-a:.6f},atrim=duration={b-a:.6f},afade=t=in:d={fade},afade=t=out:st={b-a-fade}:d={fade}[a{i}]')
        audio_inputs.append(f'[a{i}]')
    # Independent concatenation prevents rounded video frames from adding silence
    # to each audio cut. Output duration remains governed by exact audio samples.
    filters.append(''.join(audio_inputs)+f'concat=n={len(segments)}:v=0:a=1[a]')
    if info['video']:
        # Preserve source timestamps across VFR footage, subtracting only removed
        # intervals. This avoids accumulating one rounded frame per concat cut.
        select='+'.join(f'gte(t,{s["start"]:.6f})*lt(t,{s["end"]:.6f})' for s in segments)
        gaps=[str(segments[0]['start'])]
        for previous,current in zip(segments,segments[1:]):
            gaps.append(f'gte(PTS*TB,{current["start"]:.6f})*{current["start"]-previous["end"]:.6f}')
        zoom=float((visual or {}).get('zoom',1))
        if not 1<=zoom<=1.4:raise ValueError('Framing magnification must be between 1 and 1.4.')
        stream=next(s for s in info['streams'] if s['codec_type']=='video')
        framing=f',crop=trunc(iw/{zoom}/2)*2:trunc(ih/{zoom}/2)*2,scale={stream["width"]}:{stream["height"]}' if zoom>1.002 else ''
        filters.append(f"[0:v]select='{select}',setpts='PTS-({' + '.join(gaps)})/TB',fps=30:start_time=0{framing}[v]")
    args=['ffmpeg','-v','error','-y','-i',source,'-filter_complex',';'.join(filters)]
    if info['video']: args+=['-map','[v]','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p']
    else: args+=['-f','lavfi','-i','color=c=0x121820:s=1280x720:r=24','-map','1:v','-c:v','libx264','-preset','veryfast','-shortest']
    args+=['-map','[a]','-c:a','aac','-b:a','160k','-t',sum(s['end']-s['start'] for s in segments),'-movflags','+faststart',output]
    run(args)
    result=probe(output)
    expected=sum(s['end']-s['start'] for s in segments)
    if abs(result['duration']-expected)>.25: raise RuntimeError('Rendered duration did not match the plan.')
    return result
