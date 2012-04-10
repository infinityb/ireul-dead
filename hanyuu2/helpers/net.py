from collections import namedtuple
from gevent import socket
from gevent.dns import resolve_ipv6, resolve_ipv4

address_tuple = namedtuple('address_tuple', 'af address')


def resolve_netloc(netloc):
    # no IPv6 for now, FIXME
    netloc_split = netloc.split(':', 1)
    hostname = netloc_split[0]
    if len(netloc_split) > 1:
        port = int(netloc_split[1])
    ipv4_results = list()
    try:
        ipv4_results.append(socket.inet_pton(socket.AF_INET, hostname))
    except socket.error:
        pass
    try:
        _, resolv_results = resolve_ipv4(hostname)
        ipv4_results.extend(resolv_results)
    except socket.error:
        pass
    def create_tuple(af, packed):
        address_host = socket.inet_ntop(af, packed)
        return address_tuple(af, (address_host, port))
    return hostname,\
            [create_tuple(socket.AF_INET, addr) for addr in ipv4_results]
