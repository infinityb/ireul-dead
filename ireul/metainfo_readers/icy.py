from collections import namedtuple
import urlparse
import re

import gevent
import gevent.queue
from gevent import socket

from ireul.helpers.icy import parse_icy
from ireul.helpers.net import resolve_netloc


class ICYMetaData(object):
    def __init__(self, raw):
        self.raw = raw
        self._data = dict(parse_icy(raw))
        assert 'StreamTitle' in self._data
        self.stream_title = self._data['StreamTitle']

    def __unicode__(self):
        return self.stream_title


def _read_headers(fh):
    header_list = list()
    while True:
        buf = fh.readline()
        if buf == "\r\n": break
        header_list.append(buf)
    return dict(h.strip().split(':', 1) for h in header_list)

def _consume_data(fh, byte_count):
    bytes_read = 0
    while True:
        bytes_read += len(fh.read(min(4096, byte_count - bytes_read)))
        if bytes_read == byte_count:
            break

def _yield_metainfo(fh):
    status_extractor = re.compile(r'.*?\s(\d+)\s\w+')
    buf = fh.readline()
    status_match = status_extractor.match(buf)
    assert status_match, "Bad status code: %r" % buf.strip()
    status_code, = status_match.groups()
    assert "200" == status_code, "Bad status code: %r" % status_code
    headers = _read_headers(fh)
    assert 'icy-metaint' in headers
    icy_meta_interval = int(headers['icy-metaint'])
    while True:
        _consume_data(fh, icy_meta_interval)
        metainfo_length = ord(fh.read(1)) * 16
        if metainfo_length:
            yield ICYMetaData(fh.read(metainfo_length))

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
    return _yield_metainfo(conn.makefile())

def get_metadata_greenlet(url):
    """Returns a queue yielding the ICY metadata"""
    out = gevent.queue.Queue()
    def icy_metadata_gloop():
        try:
            for obj in get_metadata(url):
                out.put(obj)
        except: pass
        out.put(StopIteration)
    gevent.Greenlet.spawn(icy_metadata_gloop)
    return out
