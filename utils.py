import math

INF = float("inf")
MINUS_INF = float("-inf")
NaN = float("NaN")

def sample_line(line):
    if line.labels:
        labelstr = '{{{0}}}'.format(','.join(
            ['{0}="{1}"'.format(
                k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
                for k, v in sorted(line.labels.items())]))
    else:
        labelstr = ''
    timestamp = ''
    if line.timestamp is not None:
        # Convert to milliseconds.
        timestamp = ' {0:d}'.format(int(float(line.timestamp) * 1000))
    return '{0}{1} {2}{3}\n'.format(
        line.name, labelstr, floatToGoString(line.value), timestamp)

def floatToGoString(d):
    d = float(d)
    if d == INF:
        return '+Inf'
    elif d == MINUS_INF:
        return '-Inf'
    elif math.isnan(d):
        return 'NaN'
    else:
        s = repr(d)
        dot = s.find('.')
        # Go switches to exponents sooner than Python.
        # We only need to care about positive values for le/quantile.
        if d > 0 and dot > 6:
            mantissa = '{0}.{1}{2}'.format(s[0], s[1:dot], s[dot + 1:]).rstrip('0.')
            return '{0}e+0{1}'.format(mantissa, dot - 1)
        return s