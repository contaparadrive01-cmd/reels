"""Render an injected project. No project content is stored in this repository."""
import base64,hashlib,io,json,os,subprocess,sys,urllib.request,zipfile
from pathlib import Path

def run(args,**kw):
    subprocess.run([str(x) for x in args],check=True,**kw)

def main():
    keys=sorted(k for k in os.environ if k.startswith('PROJECT_PART_'))
    raw=base64.b64decode(''.join(os.environ[k] for k in keys),validate=True)
    if hashlib.sha256(raw).hexdigest()!=os.environ['PROJECT_SHA256']:
        raise RuntimeError('Input checksum mismatch')
    root=Path('/job');root.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for member in z.infolist():
            if not (root/member.filename).resolve().is_relative_to(root):
                raise ValueError('Unsafe input archive')
        z.extractall(root)
    project=root/'visor_videomaker'
    assets=project/'assets';assets.mkdir(exist_ok=True)
    urls={'Inter.ttf':'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf','OFL.txt':'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt'}
    for name,url in urls.items():
        with urllib.request.urlopen(url,timeout=90) as response: data=response.read()
        if name.endswith('.ttf') and data[:4] not in (b'\x00\x01\x00\x00',b'OTTO'):raise ValueError('Invalid font')
        (assets/name).write_bytes(data)
    html=project/'index.html';text=html.read_text()
    text=text.replace('</head>',"<style>@font-face{font-family:'Inter';src:url('assets/Inter.ttf') format('truetype');font-weight:100 900;font-style:normal;font-display:block}</style></head>",1)
    html.write_text(text)
    out=Path('/out');out.mkdir(exist_ok=True)
    # Same production HTML, including all original CSS and vector assets.
    run([sys.executable,project/'render.py','6.6','19.72','19.94','20.10','32.8','36.8'])
    import shutil
    shutil.copytree(project/'qa',out/'qa',dirs_exist_ok=True)
    run([sys.executable,project/'build.py','--samples','8','--output',out/'video.mp4'],timeout=3600)
    run(['ffmpeg','-v','error','-i',out/'video.mp4','-f','null','-'])
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'video.mp4')]))
    (out/'metadata.json').write_text(json.dumps(meta))
    # Frame strips for reviewing the final encoded file, not only the HTML.
    run(['ffmpeg','-v','error','-y','-i',out/'video.mp4','-vf','fps=1,scale=180:320,tile=6x7','-frames:v','1',out/'contact.jpg'])
    run(['ffmpeg','-v','error','-y','-ss','19.7','-i',out/'video.mp4','-vf','fps=15,scale=270:480,tile=4x2','-frames:v','1',out/'transition.jpg'])
    print('RENDER_COMPLETE', flush=True)

if __name__=='__main__':main()
