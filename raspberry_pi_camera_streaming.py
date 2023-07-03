import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

PAGE="""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Raspberry Pi Camera | Surveillance</title>
    <meta name="keywords" content="Live footage from Raspberry Pi">
    <meta name="description" content="Surveillance">
    <meta name="format-detection" content="telephone=no">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="shortcut icon" href="https://mastersubhajit.com/assets/favicon.ico">
    <link rel="stylesheet" href="https://demo.artureanec.com/html/quadron/css/style.css">
    <!-- Load google font
    ================================================== -->
    <script>
        WebFontConfig = {
            google: { families: [ 'Roboto:300,400,400i,500,700', 'Montserrat:700'] }
        };
        (function() {
            var wf = document.createElement('script');
            wf.src = ('https:' == document.location.protocol ? 'https' : 'http') + '://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js';
            wf.type = 'text/javascript';
            wf.async = 'true';
            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(wf, s);
        })();
    </script>
    <style>
        .layout404__img {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
        }
        #live-image, #captured-image {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
    </style>
</head>
<body>
<main id="mainContent">
    <div class="layout404">
        <div class="layout404__logo"><a href="/">Surveillance</a></div>
        <div class="container">
            <div class="row">
                <div class="layout404__img">
                    <img id="live-image" src="stream.mjpg" alt="">
                </div>
                <div class="col-lg-8 offset-lg-2">
                    <button id="capture-btn" onclick="captureImage()">Capture</button>
                    <div id="captured-image"></div>
                    <a href="/" class="btn-border btn-color-01">Refresh</a>
                </div>
            </div>
        </div>
    </div>
</main>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script src="https://demo.artureanec.com/html/quadron/js/bundle.js"></script>
<script>
    function captureImage() {
        var img = document.getElementById('live-image');
        var canvas = document.createElement('canvas');
        var context = canvas.getContext('2d');
        canvas.width = img.width;
        canvas.height = img.height;
        context.drawImage(img, 0, 0);
        var imageDataUrl = canvas.toDataURL('image/jpeg');
        document.getElementById('captured-image').innerHTML = '<img src="' + imageDataUrl + '" alt="Captured Image">';
    }
</script>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='1280x720', framerate=30) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
