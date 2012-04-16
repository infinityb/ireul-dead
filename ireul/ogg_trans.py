import time
import itertools
import gevent
import gevent.queue
from ireul import stream_event
from ireul.storage import models as m


def show_event(input_event_stream):
    for event in input_event_stream:
        print repr(event)
        yield event

def make_pos_monotonic(input_event_stream):
    track_offset = None
    last_pos = 0
    for event in input_event_stream:
        if isinstance(event, stream_event.OggPageEvent):
            if event.page.position == 0: # starting a new track
                track_offset = last_pos
            event.page.position = last_pos = track_offset + event.page.position
        yield event

def make_seq_monotonic(input_event_stream):
    seq_ctr = itertools.count()
    for event in input_event_stream:
        if isinstance(event, stream_event.OggPageEvent):
            event.page.sequence = next(seq_ctr)
        yield event

def make_single_serial(input_event_stream):
    serial = random.randint(0, 2**32)
    for event in input_event_stream:
        if isinstance(event, stream_event.OggPageEvent):
            event.page.serial = serial
        yield event

def fix_header(input_event_stream):
    yield next(input_event_stream)
    for event in input_event_stream:
        event.page.first = False
        yield event

def apply_timing(input_event_stream):
    time_initial = time.time()
    for event in input_event_stream:
        if isinstance(event, stream_event.OggPageEvent):
            real_time = time.time() - time_initial
            play_time = float(event.page.position)/44100
            gevent.sleep(max(0.0, play_time - real_time))
        yield event

def page_buffer(buffer_size):
    def _page_buffer(input_event_stream):
        queue = gevent.queue.Queue(buffer_size)
        def _read_gloop():
            for event in input_event_stream:
                queue.put(event)
            queue.put(StopIteration)
        gevent.Greenlet.spawn(_read_gloop)
        return queue
    return _page_buffer

def last_played_monitor(session_factory):
    def add_play_rec(input_event_stream):
        for event in input_event_stream:
            if isinstance(event, stream_event.TrackEndedEvent):
                session = session_factory()
                try:
                    tr_orig = session.merge(event.track.original)
                    tp = m.TrackPlay(tr_orig)
                    session.add(tp)
                    session.commit()
                finally:
                    session.close()
            yield event
    return add_play_rec

def get_now_playing_pair():
    np_command_signal = gevent.queue.Queue()
    np_command_data = gevent.queue.Queue()

    def get_now_playing_func():
        np_command_signal.put(None)
        return np_command_data.get()

    def now_playing_pipeline(input_event_stream):
        track = None
        pos_cur = None
        for event in input_event_stream:
            if not np_command_signal.empty():
                np_command_signal.get()
                np_command_data.put((track, pos_cur))
            if isinstance(event, stream_event.OggPageEvent):
                pos_cur = event.pos_cur
            if isinstance(event, stream_event.TrackStartedEvent):
                track = event.track
            yield event
    return get_now_playing_func, now_playing_pipeline

