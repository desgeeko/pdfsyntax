""" """

MIN_SEP_DISTANCE = 5


def basic_layout_test(tz):
    """ """
    res = ''
    tz.sort(key=lambda x: -(int(x[0][5]*1000) + int(x[0][4]/1000)))
    i = 1
    if tz:
        res += tz[i-1][1]
    while i < len(tz):
        if tz[i][0][5] == tz[i-1][0][5]:
            if tz[i][0][4] > tz[i-1][2][4] + MIN_SEP_DISTANCE:
                res = res + ' ' + tz[i][1]
            else:
                res = res + tz[i][1]
            del tz[i-1]
        else:
            res = res + '\n' + tz[i][1]
            i+=1
    return res


def print_debug(tfs):
    """ """
    tfs.sort(key=lambda x: -(int(x[0][5]*1000) + int(x[0][4]/1000)))
    for x in tfs:
        print(f"X {x[0][4]} Y {x[0][5]} d[{x[2][4]-x[0][4]}] | {x[1]}")
    return

