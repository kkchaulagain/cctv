import io
import picamera
from threading import Condition

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)
        
def start_camera(output, resolution='640x480', framerate=24):
    camera = picamera.PiCamera(resolution=resolution, framerate=framerate)
    camera.start_recording(output, format='mjpeg')
    return camera
