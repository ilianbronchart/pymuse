import queue
from moderngl_window import WindowConfig, run_window_config
from moderngl_window import geometry
import json
import threading
from src.config import WINDOW_POSITION_FILE, IPC_CONN
from multiprocessing.connection import Listener, Client


class Sketch(WindowConfig):
    gl_version = (3, 3)
    window_size = (800, 600)
    resource_dir = 'resources'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.close_queue = queue.Queue()
        self.close_func = self.close

        # Load and set window position
        x, y = self.load_window_position()
        self.wnd.position = (x, y)

        self.start_ipc()

    def start_ipc(self):
        def listen():
            listener = Listener(IPC_CONN)
            conn = listener.accept()
            
            while True:
                msg = conn.recv()
                print("Received message:", msg)
                if msg == 'close':
                    self.close_queue.put('close')
                if msg == 'end_listener':
                    conn.close()
                    break

            listener.close()

        listener_thread = threading.Thread(target=listen)
        listener_thread.start()

    def stop_ipc(self):
        try:
            print("Sending end_listener")
            conn = Client(IPC_CONN)
            conn.send('end_listener')
            conn.close()
            print("Sent end_listener")
        except ConnectionRefusedError:
            pass

    def check_close(self):
        try:
            if self.close_queue.get_nowait() == 'close':
                self.close()
        except queue.Empty:
            pass

    def close(self):
        print('Closing sketch')
        self.stop_ipc()

    def render(self, time: float, frame_time: float):
        self.check_close()

        self.draw()

    def draw(self):
        self.ctx.clear(1.0, 0.0, 0.0, 0.0)

    def load_window_position(self):
        try:
            with open(WINDOW_POSITION_FILE, 'r') as f:
                position = json.load(f)
                return position['x'], position['y']
        except (FileNotFoundError, json.JSONDecodeError):
            return 400, 200