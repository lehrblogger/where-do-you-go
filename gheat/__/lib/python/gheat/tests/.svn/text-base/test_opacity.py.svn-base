from gheat.opacity import _build_zoom_mapping 


def fixed(d):
    """Given a dictionary, return a guaranteed-order list of tuples.
    """
    return [(k,v) for k,v in sorted(d.items())]


def test_basic():
    conf = dict()
    conf['zoom_opaque'] = '0'
    conf['zoom_transparent'] = '4'
    expected = [ (0,255)
               , (1,191)
               , (2,127)
               , (3,63)
               , (4,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 4))
    assert actual == expected, actual

def test_unclean():
    conf = dict()
    conf['zoom_opaque'] = '0'
    conf['zoom_transparent'] = '5'
    expected = [ (0,255)
               , (1,204)
               , (2,153)
               , (3,102)
               , (4,51)
               , (5,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 5))
    assert actual == expected, actual

"""

Test these situations:

 1. equal           [(-----------)]
 2. aligned left    [(-------)xxxx]
 3. aligned right   [xxxx(-------)]
 4. over both     (-[-------------]-)
 5. over left     (-[--------)xxxx]
 6.               (-[------------)]
 7. over right      [xxxx(--------]-)
 8.                 [(------------]-)
 9. smaller         [x(-------)xxx]

"""

def test_1(): # [(-----------)]
    pass # taken care of above in _basic and _unclean

def test_2(): # [(-------)xxxx]
    conf = dict()
    conf['zoom_opaque'] = '0'
    conf['zoom_transparent'] = '4'
    expected = [ (0,255)
               , (1,191)
               , (2,127)
               , (3,63)
               , (4,0)
               , (5,0)
               , (6,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 6))
    assert actual == expected, actual

def test_3(): # [xxxx(-------)]
    conf = dict()
    conf['zoom_opaque'] = '2'
    conf['zoom_transparent'] = '6'
    expected = [ (0,255)
               , (1,255)
               , (2,255)
               , (3,191)
               , (4,127)
               , (5,63)
               , (6,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 6))
    assert actual == expected, actual

def test_4(): # (-[-------------]-)
    conf = dict()
    conf['zoom_opaque'] = '-1'
    conf['zoom_transparent'] = '4'
    expected = [ (0,204)
               , (1,153)
               , (2,102)
               , (3,51)
                ]
    actual = fixed(_build_zoom_mapping(conf, 3))
    assert actual == expected, actual

def test_5(): # (-[--------)xxxx]
    conf = dict()
    conf['zoom_opaque'] = '-1'
    conf['zoom_transparent'] = '4'
    expected = [ (0,204)
               , (1,153)
               , (2,102)
               , (3,51)
               , (4,0)
               , (5,0)
               , (6,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 6))
    assert actual == expected, actual

def test_6(): # (-[------------)]
    conf = dict()
    conf['zoom_opaque'] = '-1'
    conf['zoom_transparent'] = '4'
    expected = [ (0,204)
               , (1,153)
               , (2,102)
               , (3,51)
               , (4,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 4))
    assert actual == expected, actual

def test_7(): # [xxxx(--------]-)
    conf = dict()
    conf['zoom_opaque'] = '2'
    conf['zoom_transparent'] = '6'
    expected = [ (0,255)
               , (1,255)
               , (2,255)
               , (3,191)
               , (4,127)
                ]
    actual = fixed(_build_zoom_mapping(conf, 4))
    assert actual == expected, actual

def test_8(): # [(------------]-)
    conf = dict()
    conf['zoom_opaque'] = '0'
    conf['zoom_transparent'] = '5'
    expected = [ (0,255)
               , (1,204)
               , (2,153)
               , (3,102)
                ]
    actual = fixed(_build_zoom_mapping(conf, 3))
    assert actual == expected, actual

def test_9(): # [x(-------)xxx]
    conf = dict()
    conf['zoom_opaque'] = '2'
    conf['zoom_transparent'] = '6'
    expected = [ (0,255)
               , (1,255)
               , (2,255)
               , (3,191)
               , (4,127)
               , (5,63)
               , (6,0)
               , (7,0)
               , (8,0)
               , (9,0)
                ]
    actual = fixed(_build_zoom_mapping(conf, 9))
    assert actual == expected, actual

