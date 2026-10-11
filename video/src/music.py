import numpy as np, wave, sys
SR=44100; BPM=120; BEAT=60/BPM; BAR=4*BEAT; DUR=120.0
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def midi(m): return 440*2**((m-69)/12)
def add(sig,t,gain=1.0,pan=0.0):
    i=int(t*SR); 
    if i>=N: return
    s=sig[:N-i]*gain
    L[i:i+len(s)]+=s*(1-pan)*0.5*2**0.5*0.7; R[i:i+len(s)]+=s*(1+pan)*0.5*2**0.5*0.7
def env(n,a,d):
    t=np.arange(n)/SR; return np.minimum(1,t/max(a,1e-4))*np.exp(-t/d)
def lp(x,c):
    y=np.zeros_like(x); a=c; acc=0.0
    # vectorised one-pole via lfilter-like loop is slow; use scipy if present
    from scipy.signal import lfilter
    return lfilter([a],[1,-(1-a)],x)
from scipy.signal import lfilter, butter
def hp(x,f): b,a=butter(2,f/(SR/2),'high'); return lfilter(b,a,x)
def bpf(x,f1,f2): b,a=butter(2,[f1/(SR/2),f2/(SR/2)],'band'); return lfilter(b,a,x)
# progression Am F C G (one chord per bar)
prog=[[57,60,64],[53,57,60],[48,52,55,60],[55,59,62]]
roots=[45,41,36,43]
def section(bar):
    t=bar*BAR
    if t<8: return 'intro'
    if t<16: return 'build'
    if 16<=t<20: return 'break'
    if t<44: return 'main'
    if t<48: return 'break2'
    if t<98: return 'drop'
    if t<102: return 'break'
    if t<114: return 'drop'
    return 'outro'
nb=int(DUR/BAR)
for bar in range(nb):
    t0=bar*BAR; sec=section(bar); ch=prog[bar%4]; rt=roots[bar%4]
    # pad
    n=int(BAR*SR*1.05); tt=np.arange(n)/SR; pad=np.zeros(n)
    for m in ch:
        for det in (-0.12,0.12):
            f=midi(m+12)*2**(det/12); ph=(tt*f)%1; pad+=2*ph-1
    pad=lp(pad,0.04)*np.minimum(1,tt/0.25)*np.minimum(1,(BAR*1.05-tt)/0.2).clip(0)
    pg={'intro':0.10,'build':0.09,'break':0.12,'break2':0.11,'main':0.07,'drop':0.06,'outro':0.10}[sec]
    if sec=='outro': pg*=max(0,1-(t0-114)/6)
    add(pad,t0,pg,0)
    # bass 8ths
    if sec in('main','drop','build'):
        for k in range(8):
            n=int(BEAT/2*SR); tt=np.arange(n)/SR; f=midi(rt-12+(12 if k%2 else 0)*(sec=='drop'))
            s=np.sin(2*np.pi*f*tt)+0.4*np.sign(np.sin(2*np.pi*f*tt)); s=lp(s,0.08)*env(n,0.005,0.12)
            add(s,t0+k*BEAT/2,0.22 if sec!='build' else 0.14)
    # kick
    if sec in('build','main','drop'):
        for k in range(4):
            n=int(0.35*SR); tt=np.arange(n)/SR; f=50+110*np.exp(-tt*30)
            s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9); add(s,t0+k*BEAT,0.55)
    # clap on 2,4
    if sec in('main','drop'):
        for k in (1,3):
            n=int(0.2*SR); s=bpf(rng.standard_normal(n),900,4000)*env(n,0.001,0.06); add(s,t0+k*BEAT,0.35,0.1)
    # hats offbeat + 16ths in drop
    if sec in('build','main','drop'):
        steps=16 if sec=='drop' else 8
        for k in range(steps):
            n=int(0.06*SR); s=hp(rng.standard_normal(n),7000)*env(n,0.001,0.015)
            g=0.12 if (k*(16//steps))%4==2 else 0.05
            add(s,t0+k*BAR/steps,g,0.3 if k%2 else -0.3)
    # arp plucks
    if sec in('intro','drop','break2','main','outro'):
        notes=ch+[ch[0]+12]
        seq=[0,1,2,3,2,1,2,3]*2
        st=16 if sec=='drop' else 8
        for k in range(st):
            m=notes[seq[k]%len(notes)]+12; n=int(0.3*SR); tt=np.arange(n)/SR; f=midi(m)
            s=(np.sin(2*np.pi*f*tt)+0.3*np.sin(4*np.pi*f*tt))*env(n,0.002,0.09)
            g={'intro':0.07,'drop':0.06,'break2':0.06,'main':0.04,'outro':0.05}[sec]
            if sec=='outro': g*=max(0,1-(t0-114)/6)
            add(s,t0+k*BAR/st,g,0.4 if k%2 else -0.4)
# risers & impacts
def riser(t_end,d):
    n=int(d*SR); tt=np.arange(n)/SR; s=rng.standard_normal(n)
    out=np.zeros(n)
    for j in range(8):
        a=j*n//8;b=(j+1)*n//8; f=500+j*900; out[a:b]=bpf(s[a:b],f,f*1.6)
    add(out*(tt/d)**2,t_end-d,0.25)
def impact(t):
    n=int(1.2*SR); tt=np.arange(n)/SR; s=np.sin(2*np.pi*np.cumsum(45+60*np.exp(-tt*8))/SR)*np.exp(-tt*3)
    s+=lp(rng.standard_normal(n),0.05)*np.exp(-tt*4)*0.6; add(s,t,0.5)
for te,d in ((8,2),(20,2),(48,4),(56,2),(102,2)): riser(te,d)
for t in (8,16,20,44,48,56,98,102): impact(t)
# swishes at scene cuts
for t in (26,32,38,70,84,110,115):
    n=int(0.4*SR); tt=np.arange(n)/SR; s=bpf(rng.standard_normal(n),2000,6000)*np.sin(np.pi*tt/0.4)**2; add(s,t-0.2,0.12)
# simple stereo delay
from numpy import roll
d=int(BEAT*0.75*SR); L2=L.copy(); R2=R.copy(); L2[d:]+=0.25*R[:-d]; R2[d:]+=0.25*L[:-d]
st=np.stack([L2,R2],1); fade=int(1.5*SR); st[-fade:]*=np.linspace(1,0,fade)[:,None]
st/=np.abs(st).max()*1.12
st=np.tanh(st*1.3)/np.tanh(1.3)
st*=0.89
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
