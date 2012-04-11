import urlparse
from hanyuu2.helpers.net import resolve_netloc
from gevent import socket


def send_stream(url, source_file):
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
    conn.send("User-Agent: hanyuu2\r\n")
    conn.send("Content-Type: application/ogg\r\n")
    conn.send("\r\n")

    fileobj = conn.makefile()
    print fileobj.readline()
    print fileobj.readline()

    fh = open(source_file, 'rb')
    while True:
        buf = fh.read(4096)
        if not buf:
            fh.seek(0)
        fileobj.write(buf)

