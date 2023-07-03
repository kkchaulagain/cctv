from .camera import StreamingOutput, start_camera
from .server import StreamingServer, StreamingHandler

def main():
    output = StreamingOutput()
    camera = start_camera(output)

    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()

if __name__ == '__main__':
    main()
