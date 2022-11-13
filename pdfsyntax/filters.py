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
    """ """
    res = stream
    if '/Filter' in stream_def and stream_def['/Filter'] == '/FlateDecode':
        res = zlib.decompress(stream)
    if '/DecodeParms' in stream_def and '/Predictor' in stream_def['/DecodeParms']:
        predictor = int(stream_def['/DecodeParms']['/Predictor'])
        columns = int(stream_def['/DecodeParms']['/Columns'])
        res = decode_predictor(res, predictor, columns)
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


def asciihex(stream):
    """ """
    return (binascii.hexlify(stream)).upper()

