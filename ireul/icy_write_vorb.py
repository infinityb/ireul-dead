import time
import itertools
import gevent
import urlparse
from ireul.helpers.net import resolve_netloc
from gevent import socket
from mutagen.ogg import OggPage
from mutagen.oggvorbis import OggVorbisInfo, TryNextPage
from cStringIO import StringIO

compose = lambda *fx: reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), fx)

def yield_pages(fh):
    while True:
        try:
            yield OggPage(fh)
        except EOFError:
            break

def ogg_make_monotonic(input_page_stream):
    seq_ctr = itertools.count()
    for page in input_page_stream:
        page.sequence = next(seq_ctr)
        yield page

def monitor_position(input_page_stream):
    page = next(input_page_stream)
    yield page
    prev_pos = page.position
    time_sum =0 
    for page in input_page_stream:
        delta = page.position - prev_pos
        time_sum += float(delta)/44100
        print "(serial=%d) seq_delta = %d, ~~%0.3fs"  % (
                page.serial, delta, float(delta)/44100)
        prev_pos = page.position
        yield page
    print "total position = %d" % prev_pos
    print "total time = %dm:%02.2fs" % divmod(time_sum, 60)

def apply_timing(input_page_stream):
    time_initial = time.time()
    ovi = None
    for page in input_page_stream:
        try:
            # if we get an info page, reset counters
            ovi = OggVorbisInfo(None, page=page)
            time_initial = time.time()
        except TryNextPage:
            pass
        real_time = time.time() - time_initial
        play_time = float(page.position)/ovi.sample_rate
        gevent.sleep(max(0.0, play_time - real_time))
        yield page

def monitor_info_pages(input_page_stream):
    for page in input_page_stream:
        try:
            ovi = OggVorbisInfo(None, page=page)
            print "OggVorbisInfo = %r" % ovi
        except TryNextPage: pass
        yield page


def send_stream(url, source_file_iter):
    """Returns an iterable yielding the ICY metadata"""
    parse_result = urlparse.urlparse(url)
    hostname, addresses = resolve_netloc(parse_result.netloc)
    conn = None
    for af, address in addresses:
        conn = socket.socket(af, socket.SOCK_STREAM)
        try:
            conn.connect(address)
            break
        except socket.error:
            continue
    conn.send("SOURCE {mount} HTTP/1.0\r\n".format(mount=parse_result.path))
    conn.send("Authorization: Basic c291cmNlOmNvY2ttZQ==\r\n")
    conn.send("HOST: {hostname}\r\n".format(hostname=hostname))
    conn.send("User-Agent: ireul\r\n")
    conn.send("Content-Type: application/ogg\r\n")
    conn.send("\r\n")

    fileobj = conn.makefile()
    print fileobj.readline()
    print fileobj.readline()

    for filename in source_file_iter:
        ogg_stream = compose(ogg_make_monotonic, apply_timing, yield_pages)
        for page in ogg_stream(open(filename, 'rb')):
            fileobj.write(page.write())


src = ['/tmp/ireul/blob/3a/3a969d63c45de5f74bc6d9bcb956da03b2e4f829d2659bea5b7f411e8b21c078']

send_stream('http://vita.ib.ys:8000/cocks.ogg', src)

