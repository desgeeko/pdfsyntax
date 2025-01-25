""" """

from .objects import *
from copy import deepcopy

IDENTITY_MATRIX = [1, 0, 0, 1, 0, 0]


def multiply_matrices(m1: list, m2: list) -> list:
    """Multiply two 3x3 matrices to produce the new ctm.

    A matrix is defined by 6 variables:
    [ a b 0 ]
    [ c d 0 ]
    [ e f 1 ]
    """
    a1, b1, c1, d1, e1, f1 = m1[0], m1[1], m1[2], m1[3], m1[4], m1[5]
    a2, b2, c2, d2, e2, f2 = m2[0], m2[1], m2[2], m2[3], m2[4], m2[5]
    a = a1 * a2 + b1 * c2
    b = a1 * b2 + b1 * d2
    c = c1 * a2 + d1 * c2
    d = c1 * b2 + d1 * d2
    e = e1 * a2 + f1 * c2 + e2
    f = e1 * b2 + f1 * d2 + f2
    return [a, b, c, d, e, f]


def trm(ts, gs):
    """Text rendering matrix."""
    c = [ts['Tfs']*ts['Th']/100, 0, 0, ts['Tfs'], 0, ts['Trise']]
    res = multiply_matrices(c, ts['tm'])
    res = multiply_matrices(res, gs[-1]['ctm'])
    return res


def apply_command(command: list, graphics_state_stack: list, text_state: dict):
    """ """
    if not graphics_state_stack:
        graphics_state_stack.append({'ctm': IDENTITY_MATRIX})
    if not text_state:
        text_state['tm'] = IDENTITY_MATRIX
        text_state['tlm'] = IDENTITY_MATRIX
        text_state['Tc'] = 0
        text_state['Tw'] = 0
        text_state['Th'] = 100
        text_state['Tl'] = 0
        text_state['Tf'] = None
        text_state['Tfs'] = None
        text_state['Tmode'] = 0
        text_state['Trise'] = 0
    current_state = graphics_state_stack[-1]
    if command[-1] == 'q':
        state_backup = deepcopy(current_state)
        graphics_state_stack.append(state_backup)
    elif command[-1] == 'Q':
        graphics_state_stack.pop()
    elif command[-1] == 'cm':
        operands = command[:7]
        new_ctm = multiply_matrices(operands, current_state['ctm'])
        current_state['ctm'] = new_ctm
        #print(f"CTM ====> {current_state['ctm']}")
    elif command[-1] == 'Tc': # character spacing
        text_state['Tc'] = command[0]
    elif command[-1] == 'Tw': # word spacing
        text_state['Tw'] = command[0]
    elif command[-1] == 'Tz': # horizontal spacing
        text_state['Th'] = command[0]
    elif command[-1] == 'TL': # text leading
        text_state['Tl'] = command[0]
    elif command[-1] == 'Tf': # text font & size
        text_state['Tf'] = command[0]
        text_state['Tfs'] = command[1]
    elif command[-1] == 'Tr': # text rendering mode
        text_state['Tmode'] = command[0]
    elif command[-1] == 'Ts': # text rise
        text_state['Trise'] = command[0]
    elif command[-1] == 'BT':
        text_state['tm'] = IDENTITY_MATRIX
        text_state['tlm'] = IDENTITY_MATRIX
        #print(f"Tm ====> {text_state['tm']}")
    elif command[-1] == 'Td':
        operands = [1, 0, 0, 1, command[0], command[1]]
        tlm = text_state['tlm']
        new_m = multiply_matrices(operands, tlm)
        text_state['tm'] = new_m
        text_state['tlm'] = new_m
        #print(f"Tm ====> {text_state['tm']}")
    elif command[-1] == 'TD':
        apply_command([-command[1], 'TL'], graphics_state_stack, text_state)
        apply_command([command[0], command[1], 'Td'], graphics_state_stack, text_state)
    elif command[-1] == 'Tm':
        operands = command[:7]
        new_m = multiply_matrices(operands, IDENTITY_MATRIX)
        text_state['tm'] = new_m
        text_state['tlm'] = new_m
        #print(f"Tm ====> {text_state['tm']}")
    elif command[-1] == 'T*':
        apply_command([0, -text_state['Tl'], 'Td'], graphics_state_stack, text_state)
    elif command[-1] == "'":
        apply_command(['T*'], graphics_state_stack, text_state)
    elif command[-1] == '"':
        apply_command([command[0], 'Tw'], graphics_state_stack, text_state)
        apply_command([command[1], 'Tc'], graphics_state_stack, text_state)
        apply_command(["'"], graphics_state_stack, text_state)
    return


def parse_stream_content(content_stream: bytes) -> list:
    """Break down stream content into a list of commands.

    A command is a list made of operands followed by an operator, like [1, 0, 0, 1, 0, 0, 'cm']
    """
    ret = []
    tokens = parse_obj(b'[' + content_stream + b']')
    i = len(tokens) - 1
    section = None
    current = []
    while i >= 0:
        if type(tokens[i]) == str and tokens[i][0:1] != '/':
            if current:
                ret.insert(0, current)
            current = [tokens[i]]
            i -= 1
            continue
        if type(tokens[i]) != str or tokens[i][0:1] == '/':
            current = [tokens[i]] + current
            if i == 0 and current:
                ret.insert(0, current)
            i -= 1
            continue
            i -= 1
        i -= 1
    if current:
        ret.insert(0, current)
    return ret


def printable_stream_content(content_stream: bytes, escape = True) -> str:
    """."""
    ret = ''
    c = content_stream
    for i in range(len(c)):
        if c[i] < 20 and c[i] != 10 and c[i] != 13:
            return None
    ret = c.decode('latin-1')
    if escape:
        ret = ret.replace('<', '&lt;')
        ret = ret.replace('>', '&gt;')
    return ret


