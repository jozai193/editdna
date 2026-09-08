import numpy as np
import pytest
from engine.learning import align, make_plan, duplicate_groups, learn
from engine.media import RATE, speech_regions

def voiced(seed,duration=.5):
    rng=np.random.default_rng(seed)
    x=rng.normal(0,.16,int(RATE*duration)).astype(np.float32)
    return x*np.sin(np.linspace(0,np.pi,len(x)))

def test_alignment_locates_discontinuous_source():
    a,b,c=voiced(1),voiced(2),voiced(3);pause=np.zeros(RATE)
    raw=np.concatenate([a,pause,b,pause,c])
    final=np.concatenate([a,np.zeros(int(RATE*.15)),c])
    result=align(raw,final)
    assert len(result['matches'])==2
    assert result['matches'][1]['raw_start']==pytest.approx(3,abs=.06)
    assert all(m['score']>.95 for m in result['matches'])

def test_equal_repeated_audio_is_unresolved():
    a=voiced(1);raw=np.concatenate([a,np.zeros(RATE),a])
    assert align(raw,a)['matches'][0]['status']=='unresolved'

def words(texts):
    return [{'word':word,'start':i*3+j*.09,'end':i*3+j*.09+.08} for i,text in enumerate(texts) for j,word in enumerate(text.split())]

def test_numbers_and_negation_not_equivalent():
    regions=[{'start':0,'end':2},{'start':3,'end':5}]
    assert duplicate_groups(regions,words(['Use sixteen points for text','Use sixty points for text']))==[]
    assert duplicate_groups(regions,words(['Do remove the backup file','Do not remove the backup file']))==[]

def test_learned_takes_preserve_unique_content():
    regions=[{'start':0,'end':2},{'start':3,'end':5},{'start':6,'end':8}]
    w=words(['Keep the light beside you','Keep the light beside you','Do not erase the source'])
    p=make_plan(regions,9,{'pause_seconds':.15,'take_preference':'last'},w)
    assert [s['id'] for s in p['segments']]==['s1','s2']
    assert 'not erase' in p['segments'][-1]['text']
    assert p['segments'][0]['end']<=6

def test_silent_input_rejected():
    assert speech_regions(np.zeros(RATE))==[]
    with pytest.raises(ValueError):make_plan([],1)

def test_learning_requires_accepted_evidence():
    with pytest.raises(ValueError):learn([{'id':'p','raw_id':'a','alignment':{'matches':[]}}])

def test_profile_changes_pauses_not_speech_bounds():
    regions=[{'start':.1,'end':1},{'start':2,'end':3}]
    tight=make_plan(regions,4,{'pause_seconds':.1})
    slow=make_plan(regions,4,{'pause_seconds':.6})
    assert tight['duration']<slow['duration']
    assert tight['segments'][0]['start']==slow['segments'][0]['start']==.1
    assert tight['segments'][0]['end']>=1

def test_zero_duration_transcript_tokens_are_not_dropped():
    from engine.learning import region_texts
    r=[{'start':0,'end':1}]
    assert region_texts(r,[{'word':'not','start':.5,'end':.5}])==['not']
