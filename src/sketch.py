import glfw
import queue
import json
import threading
from src.config import WINDOW_POSITION_FILE
from multiprocessing.connection import Listener, Client
import threading
from src.config import IPC_CONN

class Sketch:
    width = 800
    height = 600

    def __init__(self):
        if not glfw.init():
            raise Exception("glfw can not be initialized!")

        self.window = glfw.create_window(self.width, self.height, "My Sketch", None, None)

        if not self.window:
            glfw.terminate()
            raise Exception("glfw window can not be created!")

        x, y = self.load_window_position()
        glfw.set_window_pos(self.window, x, y)
        glfw.make_context_current(self.window)
        glfw.set_window_pos_callback(self.window, self.window_position_callback)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)  
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.FOCUS_ON_SHOW , glfw.FALSE)

        self.listener_running = True
        self.close_queue = queue.Queue()
        self.listener_thread = self.start_ipc()

    def start_ipc(self):
        def listen():
            listener = Listener(IPC_CONN)
            conn = listener.accept()
            
            while self.listener_running:
                msg = conn.recv()
                if msg == 'close':
                    self.close_queue.put('close')
                    conn.close()
                    break

            listener.close()

        listener_thread = threading.Thread(target=listen)
        listener_thread.start()
        return listener_thread

    def poll_ipc_close(self):
        try:
            if self.close_queue.get_nowait() == 'close':
                self.close()
        except queue.Empty:
            pass
    
    def close(self):
        self.listener_running = False
        glfw.set_window_should_close(self.window, True)
        
    def run(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.poll_ipc_close()
            self.draw()
            glfw.swap_buffers(self.window)

        glfw.terminate()

    def draw(self):
        pass

    def window_position_callback(self, window, x, y):
        # Get the size of the primary monitor's screen
        primary_monitor = glfw.get_primary_monitor()
        monitor_mode = glfw.get_video_mode(primary_monitor)
        screen_width, screen_height = monitor_mode.size.width, monitor_mode.size.height

        # Ensure x and y are within the screen bounds
        x = max(0, min(x, screen_width))
        y = max(0, min(y, screen_height))

        # Debounce the saving of window position
        if hasattr(self, '_window_position_debounce') and self._window_position_debounce.is_alive():
            self._window_position_debounce.cancel()
        self._window_position_debounce = threading.Timer(0.3, self.save_window_position, [x, y])
        self._window_position_debounce.start()

    def save_window_position(self, x, y):
        with open(WINDOW_POSITION_FILE, 'w') as f:
            json.dump({'x': x, 'y': y}, f)

    def load_window_position(self):
        try:
            with open(WINDOW_POSITION_FILE, 'r') as f:
                position = json.load(f)
                return position['x'], position['y']
        except (FileNotFoundError, json.JSONDecodeError):
            return 400, 200