import os, json, copy
# from func_timeout import func_set_timeout
import Config
from utils import FileUtils, StringUtils, Logger
from VerilogAnalyzer import VcdAnalyzer, SignalAnalyzer, AstAnalyzer, DataFlowAnalyzer
from Locator.Locator import Locator
# from Adapter.Adapter import Adapter

import difflib
def string_similar(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

def groupActions(allSuspiciousSignals, allActions, allParameterInfos):
    retSuspiciousSignals, retActions, retParameterInfos = [], [], []
    for ms in allSuspiciousSignals.keys():
        for mis, act, par in zip(allSuspiciousSignals[ms], allActions[ms], allParameterInfos[ms]):
            retSuspiciousSignals.append([mis])
            retActions.append([act])
            retParameterInfos.append([par])
    return retSuspiciousSignals, retActions, retParameterInfos

def DebugWithMismatch(benchmark,bugInfo,logger):
    srcFiles = bugInfo["src_file"]
    benchmark.updateSrcFiles(srcFiles)

    benchmark.test(srcFiles=srcFiles)
    oracleVcdFile, simVcdFile, timeScale = benchmark.readVcd()

    allTerms, allBindDicts, allParameters = {}, {}, {}
    logger.info("AST parsing.")
    astArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"]}
    logger.info(astArgs)
    astParser = AstAnalyzer.AstParser(astArgs)
    logger.info("AST parsing done.")
    ast = astParser.getAst()
    logger.info("AST done.")
    fileToModulesMap = AstAnalyzer.mapFileToModule(astArgs)
    lineGapMap = StringUtils.mapLineGapAfterProcess(astArgs)
    
    dfArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"], "noreorder":True, "nobind":False}

    for module, _ in bugInfo["top_module"].items():
        logger.info("Dataflow analyzing {}.".format(module))
        dfArgs["topmodule"] = module
        dfAnalyzer = DataFlowAnalyzer.DataFlowAnalyzer(dfArgs)
        terms = dfAnalyzer.getTerms()
        bindDicts = dfAnalyzer.getBindDicts()
        parameters = dfAnalyzer.getParameters()
        allTerms.update(terms)
        allBindDicts.update(bindDicts)
        allParameters.update(parameters)

    moduleInfo = VcdAnalyzer.getModuleInfo(bugInfo["top_module"])
    
    IOports = AstAnalyzer.getIOSignals(ast, logger)

    timeStamp, mismatchSignals, simVarsDict, attributesDict, oracleAttributesDict, prevSimSignalValue, tmpSimSignalValue, tmpOracleSignalValue = VcdAnalyzer.getMismatchSignal(oracleVcdFile, simVcdFile, timeScale, logger)
    return mismatchSignals


def locate(benchmark, bugInfo, logger):
    srcFiles = bugInfo["src_file"]
    benchmark.updateSrcFiles(srcFiles)

    benchmark.test(srcFiles=srcFiles)

    oracleVcdFile, simVcdFile, timeScale = benchmark.readVcd()

    allTerms, allBindDicts, allParameters = {}, {}, {}

    astArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"]}
    astParser = AstAnalyzer.AstParser(astArgs)
    ast = astParser.getAst()
    fileToModulesMap = AstAnalyzer.mapFileToModule(astArgs)
    lineGapMap = StringUtils.mapLineGapAfterProcess(astArgs)
    
    dfArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"], "noreorder":True, "nobind":False}

    for module, _ in bugInfo["top_module"].items():
        logger.info("Dataflow analyzing {}.".format(module))
        dfArgs["topmodule"] = module
        dfAnalyzer = DataFlowAnalyzer.DataFlowAnalyzer(dfArgs)
        terms = dfAnalyzer.getTerms()
        bindDicts = dfAnalyzer.getBindDicts()
        parameters = dfAnalyzer.getParameters()
        allTerms.update(terms)
        allBindDicts.update(bindDicts)
        allParameters.update(parameters)

    moduleInfo = VcdAnalyzer.getModuleInfo(bugInfo["top_module"])
    
    IOports = AstAnalyzer.getIOSignals(ast, logger)
    
    timeStamp, mismatchSignals, simVarsDict, attributesDict, oracleAttributesDict, prevSimSignalValue, tmpSimSignalValue, tmpOracleSignalValue = VcdAnalyzer.getMismatchSignal(oracleVcdFile, simVcdFile, timeScale, logger)
    logger.info("mismatchSignals: {}".format(mismatchSignals))
    VcdAnalyzer.groupSimVarsDict(simVarsDict)
    VcdAnalyzer.MapIOSignals(simVarsDict, mismatchSignals, tmpOracleSignalValue)
    tmpInputSignalValues = VcdAnalyzer.getInputSignalValue(attributesDict, prevSimSignalValue, tmpSimSignalValue)
    # get input value for internal signals
    internalSignals = VcdAnalyzer.getInternalSignals(simVarsDict, oracleAttributesDict)
    tmpInputInternalSignalValues = VcdAnalyzer.getInputValueOfInternalSignals(timeStamp, internalSignals, simVcdFile, timeScale)
    tmpInputSignalValues.update(tmpInputInternalSignalValues)

    locator = Locator(timeStamp, mismatchSignals, bindDicts, terms, parameters, moduleInfo)
    locator.locate(tmpInputSignalValues, tmpOracleSignalValue, logger)
    suspiciousNodeIds = locator.getSpsNodeIds()
    suspiciousLinenos, suspiciousCodeLines = AstAnalyzer.getSpsLineno(ast, suspiciousNodeIds, fileToModulesMap, lineGapMap, logger)
    tmpLinenos = [i[1] for i in suspiciousLinenos]
    logger.info("Suspicious Lines: {}".format(tmpLinenos))

    with open(oracleVcdFile, 'r') as s1:
        with open(simVcdFile, 'r') as s2:
            sc1 = s1.readlines()
            sc2 = s2.readlines()
            score = string_similar(sc1,sc2)
    benchmark.removeSimulationFiles()
    return suspiciousLinenos, suspiciousCodeLines, score
