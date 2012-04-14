from ireul import icy_write_vorb
from ireul.helpers.net import resolve_netloc
from gevent import socket
import urlparse
from mutagen.ogg import OggPage

def yield_pages(fileobj):
    try:
        while True:
            yield OggPage(fileobj)
    except EOFError:
        pass

def get_metadata(url):
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
    conn.send("GET {mount} HTTP/1.1\r\n".format(mount=parse_result.path))
    conn.send("HOST: {hostname}\r\n".format(hostname=hostname))
    conn.send("User-Agent: ireul\r\n")
    conn.send("Icy-MetaData: 1\r\n")
    conn.send("\r\n")

    fileobj = conn.makefile()
    while True:
        buf = fileobj.readline()
        if buf == "\r\n": break
    return yield_pages(fileobj)


for _ in icy_write_vorb.monitor_position(get_metadata('http://vita.ib.ys:8000/cocks.ogg')):
    pass

