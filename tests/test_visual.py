from PIL import Image, ImageDraw
from engine import visual

def test_crop_recovered_and_blank_abstains():
    raw=Image.new('RGB',(480,270),'#172535');d=ImageDraw.Draw(raw)
    for i in range(12):
        d.rectangle((15+i*30,20+i*12,40+i*30,55+i*12),outline='white',width=3)
    result=visual.estimate(raw,visual.crop(raw,1.1).resize(raw.size))
    assert result['status']=='proposed'
    assert abs(result['zoom']-1.1)<=.01
    assert visual.estimate(raw,Image.new('RGB',raw.size,'black'))['status']=='unresolved'

def test_independent_sessions_required_for_framing():
    pair={'raw_id':'one','id':'p','visual':{'observations':[{'status':'accepted','zoom':1.1}]*12}}
    assert visual.learn([pair])['status']=='unknown'
    result=visual.learn([{**pair,'raw_id':str(i)} for i in range(3)])
    assert result['status']=='learned' and result['zoom']==1.1
