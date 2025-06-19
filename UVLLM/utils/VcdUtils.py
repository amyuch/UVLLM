import re, io, logging
from vcd.reader import TokenKind, tokenize, ScopeDecl

logger = logging.getLogger()

def computeUnitLevel(tsUnit, tsPrecision):
    tsUnitMatch = re.match(r"(\d+)(\w+)", tsUnit)
    tsPrecisionMatch = re.match(r"(\d+)(\w+)", tsPrecision)
    tsu1, tsu2 = int(tsUnitMatch[1]), tsUnitMatch[2]
    tsp1, tsp2 = int(tsPrecisionMatch[1]), tsPrecisionMatch[2]
    UnifiedUnitToNanoSecond = {"s":1000000, "ms": 1000, "ns": 1, "ps": 0.001, "fs": 0.000001}
    return tsp1 * UnifiedUnitToNanoSecond[tsp2] / (tsu1 * UnifiedUnitToNanoSecond[tsu2])

def parse(vcdFile, timeScale):
    scopes = []
    varsDict = {}
    varsChangeDict = {}
    attributesDict = {}
    timeStamp = 0
    unitLevel = computeUnitLevel(timeScale[0], timeScale[1])

    with open(vcdFile, "r") as f:
        for vcdLine in f:
            vcdBytes = vcdLine.encode('utf-8')
            tokens = tokenize(io.BytesIO(vcdBytes))
            # tlist = [i for i in tokens]

            for token in tokens:
                if token.kind == TokenKind.SCOPE:
                    scope = token.data.ident
                    scopes.append(scope)
                if token.kind == TokenKind.VAR:
                    if len(scopes) <= 1: continue # exclude the signals in testbench
                    if token.data.id_code not in varsDict:
                        varsDict[token.data.id_code] = []
                    varsDict[token.data.id_code].append("{}.{}".format(".".join(scopes[1:]), token.data.reference))
                    attributesDict["{}.{}".format(".".join(scopes[1:]), token.data.reference)] = {"size":token.data.size, "bit_index":token.data.bit_index}
                    varsChangeDict["{}.{}".format(".".join(scopes[1:]), token.data.reference)] = []
                if token.kind == TokenKind.UPSCOPE:
                    scopes.pop(-1)
                if token.kind == TokenKind.CHANGE_TIME:
                    timeStamp = token.data
                if token.kind == TokenKind.CHANGE_SCALAR or token.kind == TokenKind.CHANGE_VECTOR:
                    if token.data.id_code not in varsDict: continue
                    for signal in varsDict[token.data.id_code]:
                        dataValue = token.data.value
                        if isinstance(token.data.value, int):
                            dataValue = bin(token.data.value)[2:]
                        if attributesDict[signal]["size"] != len(dataValue):
                            if dataValue == 'x' or dataValue == 'z':
                                varsChangeDict[signal].append((timeStamp * unitLevel, "'b" + attributesDict[signal]["size"] * dataValue))
                            else:
                                varsChangeDict[signal].append((timeStamp * unitLevel, "'b" + dataValue.zfill(attributesDict[signal]["size"])))
                        else:
                            varsChangeDict[signal].append((timeStamp * unitLevel, "'b" + dataValue))
    
    return varsChangeDict, attributesDict
