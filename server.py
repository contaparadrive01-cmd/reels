"""Serve only render results; authentication is mandatory except for health."""
import hmac,json,os,shutil
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path('/out')
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/','/health'):
            self.send_response(200);self.end_headers();self.wfile.write(b'Export service ready');return
        token=os.environ.get('DOWNLOAD_TOKEN','')
        supplied=self.headers.get('Authorization','')
        if not token or not hmac.compare_digest(supplied,'Bearer '+token):
            self.send_response(403);self.end_headers();return
        allowed={'/video.mp4':('video.mp4','video/mp4'),'/contact.jpg':('contact.jpg','image/jpeg'),'/transition.jpg':('transition.jpg','image/jpeg'),'/metadata.json':('metadata.json','application/json')}
        if self.path not in allowed:self.send_response(404);self.end_headers();return
        name,mime=allowed[self.path];f=ROOT/name
        if not f.is_file():self.send_response(404);self.end_headers();return
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(f.stat().st_size));self.send_header('Cache-Control','private, no-store');self.end_headers()
        with f.open('rb') as data:shutil.copyfileobj(data,self.wfile)
    def log_message(self,format,*args):pass
if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','10000'))),Handler).serve_forever()
