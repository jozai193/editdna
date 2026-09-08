import json
import shutil
import pytest
from engine import media
from service.main import captions

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
def test_real_render_keeps_sample_timing_and_decodes(tmp_path):
    raw=tmp_path/'raw.mp4';out=tmp_path/'out.mp4'
    media.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=24:duration=4','-f','lavfi','-i','sine=frequency=600:sample_rate=48000:duration=4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',raw])
    segments=[{'start':.13,'end':.83},{'start':1.31,'end':2.03},{'start':2.81,'end':3.71}]
    info=media.render(raw,segments,out)
    expected=sum(s['end']-s['start'] for s in segments)
    assert abs(info['duration']-expected)<.07
    media.run(['ffmpeg','-v','error','-i',out,'-f','null','-'])
    samples=media.audio(out,tmp_path/'output.wav')
    assert abs(len(samples)/media.RATE-expected)<.05

def test_renderer_rejects_invalid_boundaries_before_export(tmp_path):
    raw=tmp_path/'raw.wav'
    import numpy as np
    from scipy.io import wavfile
    wavfile.write(raw,16000,np.zeros(16000,dtype=np.int16))
    with pytest.raises(ValueError):media.render(raw,[{'start':0,'end':2}],tmp_path/'bad.mp4')
