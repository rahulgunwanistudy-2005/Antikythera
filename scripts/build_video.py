"""Create the narrated demonstration from verified UI captures and slide renders.

Uses installed Apple Samantha speech locally and FFmpeg. No external narration
service, paid inference or scientific result generation is involved.
"""
import argparse,json,math,re,shutil,subprocess,tempfile,textwrap
from pathlib import Path
from scripts.build_dataset import ROOT

INTRO='Start in the first century. Antikythera lets us move through Mediterranean medicinal history and inspect how a claim changes across authors. The six stories in this view are case studies. They do not supply the statistical result. Move to the present, then open the corpus. Four acquired sources now provide nearly three thousand proposed claims, each with the source words and exact offsets. A person can review the annotation, record its historical date, and resolve the plant identity. The evidence view keeps retrieved papers separate from supporting experimental outcomes. At the final comparison, the software requires dated evidence, matched controls, and a complete follow-up window. The headline remains unavailable until those inputs pass independent audit.'


def command(args):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if result.returncode:raise RuntimeError(result.stderr[-3500:] or 'Media command failed')
    return result.stdout


def media(path):return json.loads(command(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def duration(path):
    info=media(path)
    values=[s.get('duration') for s in info['streams']]+[info.get('format',{}).get('duration')]
    for v in values:
        try:
            n=float(v)
            if n>0 and math.isfinite(n):return n
        except (ValueError,TypeError):pass
    raise RuntimeError('Narration is empty. Run with permission to use the installed speech service.')


def timestamp(t):
    ms=round(t*1000);seconds,milli=divmod(ms,1000);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
    return f'{hours:02}:{minutes:02}:{seconds:02},{milli:03}'


def captions(text,start,length):
    words=text.split();parts=[' '.join(words[i:i+13]) for i in range(0,len(words),13)]
    total=sum(len(p.split()) for p in parts);used=0;out=[]
    for part in parts:
        count=len(part.split());a=start+used/total*length;b=start+(used+count)/total*length
        out.append((a,b,'\n'.join(textwrap.wrap(part,width=49))));used+=count
    return out


def build(root=ROOT,voice='Samantha',rate=155):
    root=Path(root);folder=root/'docs/video';slides=folder/'slides';tour=folder/'tour';folder.mkdir(parents=True,exist_ok=True)
    if not shutil.which('say') or not shutil.which('ffmpeg'):raise RuntimeError('The video builder requires macOS say and FFmpeg. The script and slide inputs remain portable.')
    records=json.loads((folder/'narration.json').read_text())
    if [r['slide'] for r in records]!=list(range(1,11)):raise ValueError('Ten ordered slide narrations required')
    build_dir=Path(tempfile.mkdtemp(prefix='antikythera-video-',dir='/private/tmp'))
    events=[];clips=[];clock=0.;transcript=[]
    def narrate(name,text):
        source=build_dir/(name+'.txt');audio=build_dir/(name+'.aiff');source.write_text(text)
        command(['say','-v',voice,'-r',str(rate),'-o',str(audio),'-f',str(source)])
        return audio,duration(audio)
    def encode(name,image,audio,length):
        target=build_dir/(name+'.mp4')
        command(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(image),'-i',str(audio),'-t',str(length),'-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p','-af','apad=pad_dur=2','-r','25','-c:v','libx264','-preset','fast','-tune','stillimage','-crf','22','-c:a','aac','-ar','48000','-ac','2','-b:a','128k','-movflags','+faststart',str(target)])
        return target
    names=['year-60','year-600','year-1200','year-1800','year-2026','corpus','evidence','results']
    if all((tour/(n+'.png')).exists() for n in names):
        audio,spoken=narrate('intro',INTRO);length=max(60.,spoken+1.3)
        image_list=build_dir/'intro-images.txt';weights=[6,6,6,6,6,12,10,8]
        lines=[]
        for n,w in zip(names,weights):lines += ["file '"+str(tour/(n+'.png'))+"'",'duration '+str(length*w/60)]
        lines += ["file '"+str(tour/(names[-1]+'.png'))+"'"]
        image_list.write_text('\n'.join(lines)+'\n');target=build_dir/'intro.mp4'
        command(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(image_list),'-i',str(audio),'-t',str(length),'-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p','-af','apad=pad_dur=60','-r','25','-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-ar','48000','-ac','2','-b:a','128k',str(target)])
        clips.append(target);events+=captions(INTRO,clock,spoken);clock+=duration(target);transcript.append('Historical workspace tour\n'+INTRO)
        print('Video: historical workspace tour encoded',flush=True)
    for row in records:
        number=row['slide'];name=f'slide-{number:02}';image=slides/(name+'.png')
        if not image.is_file():raise FileNotFoundError(image)
        text=row['text'];audio,spoken=narrate(name,text);length=spoken+1.4
        clip=encode(name,image,audio,length);clips.append(clip)
        events+=captions(text,clock,spoken);clock+=duration(clip);transcript.append(f'Slide {number}\n{text}')
        print(f'Video: slide {number}/10 encoded',flush=True)
    subtitle=folder/'Antikythera-demo.srt';subtitle.write_text('\n\n'.join(f'{i}\n{timestamp(a)} --> {timestamp(b)}\n{text}' for i,(a,b,text) in enumerate(events,1))+'\n')
    concat=build_dir/'clips.txt';concat.write_text('\n'.join("file '"+str(p)+"'" for p in clips)+'\n')
    output=folder/'Antikythera-demo.mp4'
    command(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-i',str(subtitle),'-map','0:v:0','-map','0:a:0','-map','1:0','-c:v','copy','-c:a','copy','-c:s','mov_text','-disposition:s:0','default','-metadata','title=Antikythera research workspace demonstration','-metadata','comment=Local synthetic narration. Proposed records remain distinct from independently audited scientific results.','-movflags','+faststart',str(output)])
    info=media(output);seconds=duration(output)
    if seconds>600:raise ValueError('Demo exceeds ten minutes')
    types={s['codec_type'] for s in info['streams']}
    if not {'video','audio','subtitle'}<=types:raise RuntimeError('Video/audio/subtitle verification failed')
    (folder/'TRANSCRIPT.md').write_text('# Antikythera demo transcript\n\nNarration: Apple Samantha, generated locally. UI sequence uses verified local captures.\n\n'+'\n\n'.join(transcript)+'\n')
    result={'path':str(output),'duration_seconds':seconds,'voice':voice,'narration':'local synthetic speech','slides':10,'ui_captures':len(names) if len(clips)==11 else 0,'resolution':'1280x720','streams':sorted(types),'bytes':output.stat().st_size}
    (folder/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--voice',default='Samantha');p.add_argument('--rate',type=int,default=155);args=p.parse_args();build(voice=args.voice,rate=args.rate)
