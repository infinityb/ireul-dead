def _parse_key(input_, pos):
    retval = ''
    while input_[pos] != '=':
        retval += input_[pos]
        pos += 1
    pos += 1
    return retval, pos

def _parse_quoted_string(input_, pos):
    out = ''
    assert input_[pos] == "'"
    pos += 1
    while True:
        if input_[pos] == "'":
            pos += 1
            break
        elif input_[pos] == "\\":
            pos += 1
            out += input_[pos]
            pos += 1
        else:
            out += input_[pos]
            pos += 1
    return out, pos

def _parse_element(input_, pos):
    key, pos = _parse_key(input_, pos)
    val, pos = _parse_quoted_string(input_, pos)
    assert input_[pos] == ';'
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

