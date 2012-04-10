def _parse_key(input_, pos):
    retval = ''
    while input_[pos] != '=':
        retval += input_[pos]
        pos += 1
    pos += 1
    return retval, pos

def _parse_quoted_string(input_, pos):
    # apparently ICY quoted strings are not quite quoted strings,
    # they don't escape their quote, so just scan until ';
    out = ''
    assert input_[pos] == "'", "at %d in %r" % (pos, input_)
    pos += 1
    while True:
        if input_[pos:pos+2] == "';":
            pos += 1
            break
        else:
            out += input_[pos]
            pos += 1
    return out, pos

def _parse_element(input_, pos):
    key, pos = _parse_key(input_, pos)
    val, pos = _parse_quoted_string(input_, pos)
    assert input_[pos] == ';', "at %d in %r" % (pos, input_)
    pos += 1
    return (key, val), pos

def parse_icy(input_):
    input_ = input_.rstrip("\x00")
    pos = 0
    elements = list()
    while pos < len(input_):
        element, pos = _parse_element(input_, pos)
        elements.append(element)
    return elements

def _generate_icy(data):
    # I am unsure of the specification, so this will remain ugly for now.
    elements = list()
    if 'StreamTitle' in data:
        elements.append("%s='%s';" % ('StreamTitle', data['StreamTitle']))
    if 'X-Track-Id' in data:
        elements.append("%s=%s;" % ('X-Track-Id', data['X-Track-Id']))
    buf = ''.join(elements)
    buf += "\x00" * (-len(buf) % 16)
    return buf

def metainfo_injector(meta_info_getter, inject_freq, src_queue):
    # meta_info_getter should yield empty dictionaries if the status
    # has not been modified
    out_queue = gevent.queue.Queue()
    def gloop():
        # FIXME: use a ring buffer later
        buf = ''
        for read_data in src_queue.get():
            buf += read_data
            while inject_freq < len(buf):
                buf, tmp = buf[0:inject_freq], buf[inject_freq:]
                out_queue.put(tmp)
                out_queue.put(_generate_icy(meta_info_getter()))
        out_queue.put(StopIteration)

