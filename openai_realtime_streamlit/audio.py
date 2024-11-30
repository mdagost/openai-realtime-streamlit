import queue
import sounddevice as sd

class StreamingAudioRecorder:
    """
    Thanks Sonnet 3.5...
    """

    def __init__(self, sample_rate=24_000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_thread = None

    def callback(self, indata, frames, time, status):
        """
        This will be called for each audio block
        that gets recorded.
        """
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        self.is_recording = True
        self.audio_thread = sd.InputStream(
            dtype="int16",
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.callback,
            blocksize=2_000
        )
        self.audio_thread.start()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.audio_thread.stop()
            self.audio_thread.close()

    def get_audio_chunk(self):
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None