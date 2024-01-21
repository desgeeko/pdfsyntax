"""Module pdfsyntax.filters"""

import zlib
import binascii


def decode_predictor(bdata: bytes, predictor, columns): #TODO handle more PNG predictors
    """ """
    size = len(bdata)
    res = b''
    columns += 1
    prev_row = [0] * columns
    i = 0
    while i < size:
        row = list(bdata[i:i+columns])
        # Predictor 12, PNG Up
        decoded_row = [(val + prev_row[index]) & 0xff for (index, val) in enumerate(row)]
        prev_row = decoded_row
        res += bytes(decoded_row[1:])
        i += columns
    return res


def decode_stream(stream, stream_def):
    """Apply all specified filters in order to decode stream."""
    if '/Filter' not in stream_def:
        return stream
    filters = stream_def['/Filter']
    if type(filters) == str:
        filters = [filters]
    if '/DecodeParms' not in stream_def:
        parms = [None] * len(filters)
    else:
        parms = stream_def['/DecodeParms']
        if type(parms) == str:
            parms = [parms]
    res = stream
    for i, f in enumerate(filters):
        if f == '/FlateDecode':
            try:
                res = zlib.decompress(res)
                if parms[i] and '/Predictor' in parms[i]:
                    predictor = int(parms[i]['/Predictor'])
                    columns = int(parms[i]['/Columns'])
                    res = decode_predictor(res, predictor, columns)
            except:
                return b'#PDFSyntaxException: cannot decode Flate'
        else:
            return b'#PDFSyntaxException: unsupported filter'
    return res


def encode_stream(stream, stream_def):
    """ """
    if '/Filter' not in stream_def:
        return stream
    if stream_def['/Filter'] == '/FlateDecode':
        return zlib.compress(stream)
    elif stream_def['/Filter'] == '/ASCIIHexDecode':
        return asciihex(stream)
    return stream


def asciihex(stream, columns = None):
    """ """
    if columns is None:
        return (binascii.hexlify(stream)).upper()
    else:
        res = b''
        i = 0
        l = sum(columns)
        while i+l <= len(stream):
            for c in columns:
                res += (binascii.hexlify(stream[i:i+c])).upper() 
                res += b' '
                i += c
            res += b'\n'
        return res


