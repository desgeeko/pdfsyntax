"""Module pdfsyntax.filters"""

import zlib
import binascii
import base64


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
#    b1 = b'stream' + b'\r\n'
#    b2 = b'stream' + b'\n'
#    e1 = b'\r\n' + b'endstream'
#    e2 = b'\n' + b'endstream'
#    e3 = b'\r' + b'endstream'
#    if stream[:len(b1)] == b1:
#        b = len(b1)
#    elif stream[:len(b2)] == b2:
#        b = len(b2)
#    else:
#        return None
#    if stream[-len(e1):] == e1:
#        e = len(e1)
#    elif stream[-len(e2):] == e2:
#        e = len(e2)
#    elif stream[-len(e3):] == e3:
#        e = len(e3)
#    else:
#        return None
#    s = stream[b:-e]
    s = stream
    if '/Filter' not in stream_def:
        return s
    filters = stream_def['/Filter']
    if type(filters) == str:
        filters = [filters]
    if '/DecodeParms' not in stream_def:
        parms = [None] * len(filters)
    else:
        parms = stream_def['/DecodeParms']
        if type(parms) == dict:
            parms = [parms]
    #res = s
    for i, f in enumerate(filters):
        if f == '/FlateDecode':
            try:
                res = zlib.decompress(s)
                if parms[i] and '/Predictor' in parms[i]:
                    predictor = int(parms[i]['/Predictor'])
                    columns = int(parms[i]['/Columns'])
                    res = decode_predictor(res, predictor, columns)
            except:
                return b'#PDFSyntaxException: cannot decode Flate'
        elif f == '/ASCIIHexDecode':
            try:
                res = binascii.unhexlify(s)
            except:
                return b'#PDFSyntaxException: cannot decode ASCIIHex'
        elif f == '/ASCII85Decode':
            try:
                res = base64.a85decode(s, adobe=True)
            except:
                return b'#PDFSyntaxException: cannot decode ASCII85'
        else:
            return b'#PDFSyntaxException: unsupported filter'
    return res


def encode_stream(stream, stream_def):
    """Apply all specified filters in order to encode stream."""
    #b = b'stream\n'
    #e = b'\nendstream'
    if '/Filter' not in stream_def:
        return stream
    filters = stream_def['/Filter']
    if type(filters) == str:
        filters = [filters]
    res = stream
    for _, f in enumerate(filters):
        if f == '/FlateDecode':
            try:
                #res = b + zlib.compress(res) + e
                res = zlib.compress(res)
            except:
                return b'#PDFSyntaxException: cannot encode Flate'
        elif f == '/ASCIIHexDecode':
            try:
                #res = b + asciihex(res) + e
                res = asciihex(res)
            except:
                return b'#PDFSyntaxException: cannot encode ASCIIHex'
        elif f == '/ASCII85Decode':
            try:
                #res = b + base64.a85encode(res, adobe=True) + e
                res = base64.a85encode(res, adobe=True)
            except:
                return b'#PDFSyntaxException: cannot encode ASCII85'
        else:
            return b'#PDFSyntaxException: unsupported filter'
    return res


def asciihex(stream, columns = None):
    """ASCIIHex encoder augmented with a beautifier (colums and newlines) for DEBUG ONLY."""
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


