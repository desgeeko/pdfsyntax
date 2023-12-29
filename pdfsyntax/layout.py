"""Module pdfsyntax.layout: from spatial representation to text file"""


MIN_SEP_DISTANCE = 5
NEWLINE_COEFF = 3


def basic_spatial_layout(text_blocks: list) -> str:
    """Extract text."""
    res = ''
    text_blocks.sort(key=lambda tb: -tb['y'])
    min_x = minimum_x(text_blocks)
    fs = typical_font_size(text_blocks)
    spacing = typical_line_spacing(text_blocks, fs)
    #print(f"spacing = {spacing}")
    char_w = typical_char_width(text_blocks, fs)
    #print(f"char w = {char_w}")
    previous_y = -1
    while text_blocks:
        line_string = ''
        line_items = [text_blocks.pop(0)]
        target_y = line_items[0]['y']
        if previous_y != -1:
            inter_lines = int((previous_y - target_y - spacing / NEWLINE_COEFF) / spacing)
            res += '\n' * inter_lines
        previous_y = target_y
        #print("-----------------------------------")
        #print(line_items[0])
        while text_blocks:
            if abs(target_y - text_blocks[0]['y']) > spacing * 0.9:
                break
            line_items.append(text_blocks.pop(0))
            #print(line_items[-1])
        line_items.sort(key=lambda tb: tb['x'])
        #TODO exclude overlapping blocks
        nb_spaces = (int(line_items[0]['x']) - min_x) // char_w
        line_string += ' ' * int(nb_spaces)
        line_string += line_items[0]['text']
        i = 1
        while i < len(line_items):
            if line_items[i]['x'] > line_items[i-1]['x'] + line_items[i-1]['width'] + MIN_SEP_DISTANCE:
                nb_spaces = (int(line_items[i]['x']) - min_x) // char_w
                offset = len(line_string)
                line_string += ' ' * (int(nb_spaces) - offset)
            line_string += line_items[i]['text']
            i += 1
        if line_string != ' ':
            res += line_string + '\n'
    return res


def simplify_horizontal_text_elements(text_blocks: list):
    """Arrange text blocks into something more readable."""
    for i, tz in enumerate(text_blocks):
        old_trm, uc, new_trm = tz[0], tz[1], tz[2]
        x = old_trm[4]
        y = old_trm[5]
        width = new_trm[4] - old_trm[4]
        scaling = old_trm[0]
        text_blocks[i] = {'x': x, 'y': y,'width': width,'scaling': scaling,'text': uc}
    return


def most_frequent(distrib: dict):
    """Helper to get the key that points at the highest value."""
    most_frequent = 0
    max_occur = 0
    for s in distrib:
        if distrib[s] > max_occur:
            most_frequent = s
            max_occur = distrib[s]
    return most_frequent


def typical_font_size(text_blocks: list) -> float:
    """Find the most frequent font size."""
    distrib = {}
    for x in text_blocks:
        scaling = x['scaling']
        nb_char = len(x['text'])
        if scaling not in distrib:
            distrib[scaling] = 0
        distrib[scaling] += nb_char
    return most_frequent(distrib)


def minimum_x(text_blocks: list) -> float:
    """Find the minimum x coordinate of all text blocks."""
    min_x = -1
    for tb in text_blocks:
        if min_x == -1 or tb['x'] < min_x:
           min_x = tb['x']
    return min_x


def typical_line_spacing(text_blocks: list, typical_font_size: float) -> float:
    """ """
    distrib = {}
    columns = {}
    for i in text_blocks:
        if i['scaling'] != typical_font_size:
            continue
        if i['x'] not in columns:
             columns[i['x']] = []
        columns[i['x']].append(i['y'])
    for col in columns:
        if len(columns[col]) < 3:
            continue
        columns[col].sort()
        j = 0
        while j < len(columns[col]) - 1:
            delta = int((columns[col][j+1] - columns[col][j]) * 10) / 10
            if delta not in distrib:
                distrib[delta] = 0
            distrib[delta] += 1
            j += 1
    tls = most_frequent(distrib)
    if tls:
        return tls
    else:
        return typical_font_size


def typical_char_width(text_blocks: list, typical_font_size: float) -> float:
    """ """
    distrib = []
    for i in text_blocks:
        if i['scaling'] != typical_font_size or len(i['text']) < 2:
            continue
        distrib.append(i['width'] / len(i['text']))
    if len(distrib):
        return sum(distrib) / len(distrib)
    else:
        return 0


def print_debug(text_blocks: list):
    """ """
    #text_blocks.sort(key=lambda tz: -(int(tz['y']*1000)) + int(tz['x']/1000))
    for tz in text_blocks:
        print(f"X {tz['x']} Y {tz['y']} width[{tz['width']}] scaling[{tz['scaling']}] | {tz['text']}")
    return

