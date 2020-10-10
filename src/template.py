"""

Designed and Developed by-
Udayraj Deshmukh
https://github.com/Udayraj123

"""

from .constants import TEMPLATE_DEFAULTS_PATH
from .utils.file import loadJson
from .utils.object import override_merger

templateDefaults = loadJson(TEMPLATE_DEFAULTS_PATH)

def openTemplateWithDefaults(templatePath):
    user_template = loadJson(templatePath)
    return override_merger.merge(templateDefaults, user_template)

import numpy as np
from argparse import Namespace
from collections import OrderedDict  # For Python 3.5 and earlier

### Coordinates Part ###


class Pt():
    """
    Container for a Point Box on the OMR
    """
    """
    qNo is the point's property- question to which this point belongs to
    It can be used as a roll number column as well. (eg roll1)
    It can also correspond to a single digit of integer type Q (eg q5d1)
    """

    def __init__(self, pt, qNo, qType, val):
        self.x = round(pt[0])
        self.y = round(pt[1])
        self.qNo = qNo
        self.qType = qType
        self.val = val


class QBlock():
    def __init__(self, dimensions, key, orig, traverse_pts):
        # dimensions = (width, height)
        self.dimensions = tuple(round(x) for x in dimensions)
        self.key = key
        self.orig = orig
        self.traverse_pts = traverse_pts
        # will be set when using
        self.shift = 0

# TODO: get this out
qtype_data = {
    'QTYPE_MED': {
        'vals': ['E', 'H'],
        'orient': 'V'
    },
    'QTYPE_ROLL': {
        'vals': range(10),
        'orient': 'V'
    },
    'QTYPE_INT': {
        'vals': range(10),
        'orient': 'V'
    },
    'QTYPE_MCQ4': {
        'vals': ['A', 'B', 'C', 'D'],
        'orient': 'H'
    },
    'QTYPE_MCQ5': {
        'vals': ['A', 'B', 'C', 'D', 'E'],
        'orient': 'H'
    },
    #
    # You can create and append custom question types here-
    # 
}
class Template():
    def __init__(self, template_path, extensions):
        json_obj = openTemplateWithDefaults(template_path)
        self.path = template_path.name
        self.qBlocks = []
        # TODO: ajv validation - throw exception on key not exist
        # TODO: extend DotMap here and only access keys that need extra parsing
        self.dimensions = json_obj["dimensions"]
        self.bubbleDimensions = json_obj["bubbleDimensions"]
        self.concatenations = json_obj["concatenations"]
        self.singles = json_obj["singles"]

        # Add new qTypes from template
        if "qtypes" in json_obj:
            qtype_data.update(json_obj["qtypes"])

        # load image preProcessors
        self.preProcessors = [extensions[name](opts, template_path.parent) 
                              for name, opts in json_obj.get(
                                    "preProcessors", {}).items()]

        # Add options
        self.options = json_obj.get("options", {})


        # Add qBlocks
        for name, block in json_obj["qBlocks"].items():
            self.addQBlocks(name, block)


    # Expects bubbleDimensions to be set already
    def addQBlocks(self, key, rect):
        assert(self.bubbleDimensions != [-1, -1])
        # For qType defined in qBlocks
        if 'qType' in rect:
            rect.update(**qtype_data[rect['qType']])
        else:
            rect['qType'] = {'vals': rect['vals'], 'orient': rect['orient']}
        # keyword arg unpacking followed by named args
        self.qBlocks += genGrid(self.bubbleDimensions, key, **rect)
        # self.qBlocks.append(QBlock(rect.orig, calcQBlockDims(rect), maketemplate(rect)))

    def __str__(self):
        return self.path


def genQBlock(
        bubbleDimensions,
        QBlockDims,
        key,
        orig,
        qNos,
        gaps,
        vals,
        qType,
        orient,
        colOrient):
    """
    Input:
    orig - start point
    qNos  - a tuple of qNos
    gaps - (gapX,gapY) are the gaps between rows and cols in a block
    vals - a 1D array of values of each alternative for a question

    Output:
    // Returns set of coordinates of a rectangular grid of points
    Returns a QBlock containing array of Qs and some metadata?!

    Ref:
        1 2 3 4
        1 2 3 4
        1 2 3 4

        (q1, q2, q3)

        00
        11
        22
        33
        44

        (q1.1,q1.2)

    """
    H, V = (0, 1) if(orient == 'H') else (1, 0)
    # orig[0] += np.random.randint(-6,6)*2 # test random shift
    traverse_pts = []
    o = [float(i) for i in orig]

    if(colOrient == orient):
        for q in range(len(qNos)):
            pt = o.copy()
            pts = []
            for v in range(len(vals)):
                pts.append(Pt(pt.copy(), qNos[q], qType, vals[v]))
                pt[H] += gaps[H]
            # For diagonalal endpoint of QBlock
            pt[H] += bubbleDimensions[H] - gaps[H]
            pt[V] += bubbleDimensions[V]
            # TODO- make a mini object for this
            traverse_pts.append(([o.copy(), pt.copy()], pts))
            o[V] += gaps[V]
    else:
        for v in range(len(vals)):
            pt = o.copy()
            pts = []
            for q in range(len(qNos)):
                pts.append(Pt(pt.copy(), qNos[q], qType, vals[v]))
                pt[V] += gaps[V]
            # For diagonalal endpoint of QBlock
            pt[V] += bubbleDimensions[V] - gaps[V]
            pt[H] += bubbleDimensions[H]
            # TODO- make a mini object for this
            traverse_pts.append(([o.copy(), pt.copy()], pts))
            o[H] += gaps[H]
    # Pass first three args as is. only append 'traverse_pts'
    return QBlock(QBlockDims, key, orig, traverse_pts)


def genGrid(
        bubbleDimensions,
        key,
        qType,
        orig,
        bigGaps,
        gaps,
        qNos,
        vals,
        orient='V',
        colOrient='V'):
    """
    Input(Directly passable from JSON parameters):
    bubbleDimensions - dimesions of single QBox
    orig- start point
    qNos - an array of qNos tuples(see below) that align with dimension of the big grid (gridDims extracted from here)
    bigGaps - (bigGapX,bigGapY) are the gaps between blocks
    gaps - (gapX,gapY) are the gaps between rows and cols in a block
    vals - a 1D array of values of each alternative for a question
    orient - The way of arranging the vals (vertical or horizontal)

    Output:
    // Returns an array of Q objects (having their points) arranged in a rectangular grid
    Returns grid of QBlock objects

                                00    00    00    00
   Q1   1 2 3 4    1 2 3 4      11    11    11    11
   Q2   1 2 3 4    1 2 3 4      22    22    22    22         1234567
   Q3   1 2 3 4    1 2 3 4      33    33    33    33         1234567
                                44    44    44    44
                            ,   55    55    55    55    ,    1234567                       and many more possibilities!
   Q7   1 2 3 4    1 2 3 4      66    66    66    66         1234567
   Q8   1 2 3 4    1 2 3 4      77    77    77    77
   Q9   1 2 3 4    1 2 3 4      88    88    88    88
                                99    99    99    99

TODO: Update this part, add more examples like-
    Q1  1 2 3 4

    Q2  1 2 3 4
    Q3  1 2 3 4

    Q4  1 2 3 4
    Q5  1 2 3 4

    MCQ type (orient='H')-
        [
            [(q1,q2,q3),(q4,q5,q6)]
            [(q7,q8,q9),(q10,q11,q12)]
        ]

    INT type (orient='V')-
        [
            [(q1d1,q1d2),(q2d1,q2d2),(q3d1,q3d2),(q4d1,q4d2)]
        ]

    ROLL type-
        [
            [(roll1,roll2,roll3,...,roll10)]
        ]

    """
    gridData = np.array(qNos)
    # print(gridData.shape, gridData)
    if(0 and len(gridData.shape) != 3 or gridData.size == 0):  # product of shape is zero
        print(
            "Error(genGrid): Invalid qNos array given:",
            gridData.shape,
            gridData)
        exit(32)

    orig = np.array(orig)
    numQsMax = max([max([len(qb) for qb in row]) for row in gridData])

    numDims = [numQsMax, len(vals)]

    qBlocks = []

    # **Simple is powerful**
    # H and V are named with respect to orient == 'H', reverse their meaning
    # when orient = 'V'
    H, V = (0, 1) if(orient == 'H') else (1, 0)

    # print(orig, numDims, gridData.shape, gridData)
    # orient is also the direction of making qBlocks

    # print(key, numDims, orig, gaps, bigGaps, origGap )
    qStart = orig.copy()

    origGap = [0, 0]

    # Usually single row
    for row in gridData:
        qStart[V] = orig[V]

        # Usually multiple qTuples
        for qTuple in row:
            # Update numDims and origGaps
            numDims[0] = len(qTuple)
            # bigGaps is indep of orientation
            origGap[0] = bigGaps[0] + (numDims[V] - 1) * gaps[H]
            origGap[1] = bigGaps[1] + (numDims[H] - 1) * gaps[V]
            # each qTuple will have qNos
            QBlockDims = [
                # width x height in pixels
                gaps[0] * (numDims[V] - 1) + bubbleDimensions[H],
                gaps[1] * (numDims[H] - 1) + bubbleDimensions[V]
            ]
            # WATCH FOR BLUNDER(use .copy()) - qStart was getting passed by
            # reference! (others args read-only)
            qBlocks.append(
                genQBlock(
                    bubbleDimensions,
                    QBlockDims,
                    key,
                    qStart.copy(),
                    qTuple,
                    gaps,
                    vals,
                    qType,
                    orient,
                    colOrient))
            # Goes vertically down first
            qStart[V] += origGap[V]
        qStart[H] += origGap[H]
    return qBlocks