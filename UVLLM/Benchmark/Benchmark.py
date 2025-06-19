import os, re, abc, json
import configparser
import Config
from utils import VcdUtils, FileUtils, StringUtils
from VerilogAnalyzer import SignalAnalyzer

class Benchmark:
    def __init__(self, benchmark) -> None:
        self.benchmark = benchmark
        self.project = None
        self.version = None
        self.cparser = configparser.ConfigParser()
        self.cparser.read(os.path.join(Config.BENCHMARKS, "{}.conf".format(benchmark)))
        self.bugInfoDict = {}
    
    def getBugInfo(self, project, version):
        self.project = project
        self.version = version
        bugInfo = self.cparser.items("{}_{}".format(project, version))
        self.bugInfoDict = dict(bugInfo)
        for k, v in self.bugInfoDict.items():
            if k == "timeout":
                continue
            if k == "top_module": 
                self.bugInfoDict[k] = json.loads(v)
            elif v.startswith('['):
                vlist = json.loads(v)
                # 修复路径处理逻辑：确保不会重复拼接目录
                self.bugInfoDict[k] = [os.path.join(Config.PROJECT_PATH, v) for v in vlist]
            else:
                # 修复路径处理逻辑：确保不会重复拼接目录
                self.bugInfoDict[k] = os.path.join(Config.PROJECT_PATH, v)
        return self.bugInfoDict
    
    def getAllBugs(self):
        allBugs = self.cparser.sections()
        retBugs = []
        for bug in allBugs:
            rIndex = bug.rindex("_")
            proj, version = bug[:rIndex], bug[rIndex+1:]
            retBugs.append((proj, version))
        return retBugs
    
    def updateSrcFiles(self, srcFiles):
        self.bugInfoDict["src_file"] = srcFiles
    
    def getBugId(self):
        return self.benchmark, self.project, self.version

    def readSimulationOutput(self):
        oracleSignal, simSignal = SignalAnalyzer.processOutputFile(self.bugInfoDict["oracle_output"], self.bugInfoDict["sim_output"])
        return oracleSignal, simSignal

    def readVcd(self):
        testBench = FileUtils.readFileToStr(self.bugInfoDict["test_bench"])
        testBench = StringUtils.removeComment(testBench)
        includeFiles = re.findall("`include \"(.*?)\"\n", testBench)
        for includeFile in includeFiles[::-1]:
            testBench = FileUtils.readFileToStr(os.path.join(os.path.dirname(self.bugInfoDict["test_bench"]), includeFile)) + testBench
        timeScale = re.findall("`timescale (.*)/(.*)\n", testBench)
        assert len(timeScale) <= 1
        if len(timeScale) == 0:
            timeScale = ("1s", "1s")
        else:
            timeScale = (timeScale[0][0].replace(' ', ''), timeScale[0][1].replace(' ', ''))
        # oracleVcd, _ = VcdUtils.parse(self.bugInfoDict["oracle_vcd"], timeScale)
        # simVcd, simVarsDict = VcdUtils.parse(self.bugInfoDict["sim_vcd"], timeScale)
        # return oracleVcd, simVcd, simVarsDict
        return self.bugInfoDict["oracle_vcd"], self.bugInfoDict["sim_vcd"], timeScale
    
    def removeSimulationFiles(self):
        FileUtils.removeFile(self.bugInfoDict["sim_output"])
        FileUtils.removeFile(self.bugInfoDict["sim_vcd"])
    
    @abc.abstractclassmethod
    def test(self, srcFiles, tbFile):
        pass

    @abc.abstractclassmethod
    def validate(self, candidatePatch):
        pass
