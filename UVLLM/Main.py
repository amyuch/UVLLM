import sys, argparse, func_timeout, re, os, shutil
import Config
import Repair
import time
from pathlib import Path
from utils import Logger, FileUtils
from Benchmark import BenchmarkFactory

from rtlrepair import parse_verilog, serialize,  preprocess,  Status

import api

import difflib
def string_similar(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

def test_preprocess(logger,bugInfo,working_dir):
    try:
        filename, changes = preprocess(working_dir, Path("".join(bugInfo["src_file"])), Path("".join(bugInfo["include_list"])), logger)
        if changes:
            FileUtils.backupFile(str(filename), bugInfo["src_file"][0])
        logger.info("changes are {}".format(changes))
        return filename
    except func_timeout.exceptions.FunctionTimedOut:
        logger.error("Preprocess Repair timeout.")
    except Exception as e:
        logger.error("Preprocess Repair error.")
        logger.error(str(e)) 

def test_mismatch(logger, benchmark, bugInfo, working_dir, max_i):
    preprocess_time = 0
    start_time = time.time()
    gpt_try =0
    for i in range(max_i):
        try:
            iteration_starttime = time.time()
            filename = test_preprocess(logger,bugInfo,working_dir)
            iteration_preprocesstime = time.time()
            preprocess_time += iteration_preprocesstime - iteration_starttime

            orig = bugInfo["src_file"][0]
            path, src = os.path.split(orig)
            patch_dir = working_dir / "1_mismatch"
            if not patch_dir.exists():
                    os.mkdir(patch_dir)
            mismatchsignals = Repair.DebugWithMismatch(benchmark, bugInfo, logger)

            if mismatchsignals:               
                target = patch_dir/f"{src.split('.')[0]}_{i}.v"
                FileUtils.backupFile(orig, target)   

                max_try = 5
                try_api = 0
                while try_api<max_try:

                    try:
                        logger.info(filename.as_posix())
                        newcode, fix = api.api_gpt_mismatch(bugInfo["spec_file"],str(filename.as_posix()), str(mismatchsignals), None, logger)
                        
                        with open(Path("".join(bugInfo["src_file"])), 'w') as codepath:
                            codepath.write(newcode)
                        break
                    except Exception as e:
                        try_api+=1
                        logger.error("Error in api.api_gpt, retrying...")
                        logger.error(str(e))
                    

            else: #correct
                if(i==0):
                    logger.info("Finish in preprocess.")
                else:
                    logger.info("Finish in mismatch with {} iterations.".format(i))    
                FileUtils.removeDirContent(Config.WORK_DIR)
                end_time= time.time()
                total_time = end_time - start_time
                mismatch_time = total_time - preprocess_time
                return 1,preprocess_time,mismatch_time
            FileUtils.removeDirContent(Config.WORK_DIR)
        except func_timeout.exceptions.FunctionTimedOut:
            logger.error("Mismatch Repair timeout.")
        except Exception as e:
            logger.error("Mismatch exception.")
            logger.error(str(e))
            if(i==0):
                logger.info("Cannot simulation.")
                newcode, fix = api.api_syntax(str(filename.as_posix()), str(e), None, logger) #prevent the syntax error                       
                with open(Path("".join(bugInfo["src_file"])), 'w') as codepath:
                    codepath.write(newcode)
                gpt_try=1
            elif gpt_try==1:
                logger.error("Mismatch Repair error.")
                break    
            else:
                logger.error("Bad fix. Roll back to the previous version.")
                # 获取patch_dir和src
                patch_dir = os.path.join(os.path.dirname(bugInfo["src_file"][0]), "2_SuspiciousLine")
                src = os.path.basename(bugInfo["src_file"][0])
                rollback_path = os.path.join(patch_dir, f"{src.split('.')[0]}_{i-1}.v")
                if os.path.exists(rollback_path):
                    with open(rollback_path, 'r') as back: #rollback to the previous version
                        with open(bugInfo["src_file"][0], 'w') as codepath:
                            backup = back.read()
                            codepath.write(backup)
                else:
                    from utils.TerminalUtils import print_result
                    logger.error(f"Rollback file not found: {rollback_path}")
                    print_result(False, "回滚失败，补丁文件不存在", str(rollback_path))
    end_time= time.time()
    total_time = end_time - start_time
    mismatch_time = total_time - preprocess_time
    return 0,preprocess_time,mismatch_time


def test_suspiciousline(logger, benchmark, bugInfo, working_dir, history, max_i):
    preprocess_time = 0
    start_time = time.time()
    for i in range(max_i):
        try:
            iteration_starttime = time.time()
            filename = test_preprocess(logger,bugInfo,working_dir)
            iteration_preprocesstime = time.time()
            preprocess_time += iteration_preprocesstime - iteration_starttime

            orig = bugInfo["src_file"][0]
            path, src = os.path.split(orig)           
            patch_dir = working_dir / "2_SuspiciousLine"
            if not patch_dir.exists():
                os.mkdir(patch_dir)
            suspiciousLinenos, suspiciousCodeLines, score = Repair.locate(benchmark, bugInfo, logger)

            if suspiciousCodeLines:
                badfix = None
                if i>0:
                    if history[i-1]["score"] > score:
                        suspiciousCodeLines = history[i-1]["suspiciousCodeLines"]
                        badfix = history[i-1]["fix"]
                        with open(history[i-1]["codepath"], 'r') as historycode:
                            content = historycode.readlines()
                            with open(Path("".join(bugInfo["src_file"])), 'w') as codepath:
                                for con in content:
                                    codepath.write(con)
                    else:
                        history[i-1]["score"] = score
                
                target = patch_dir/f"{src.split('.')[0]}_{i}.v"
                FileUtils.backupFile(orig, target)

                max_try = 5
                try_api = 0
                while try_api<max_try:

                    try:
                        newcode, fix = api.api_gpt_suspicious(bugInfo["spec_file"],str(filename.as_posix()), str(suspiciousCodeLines), badfix, logger)           

                        logger.info("score: {}".format(score))
                        logger.info(badfix)
                        with open(Path("".join(bugInfo["src_file"])), 'w') as codepath:
                            codepath.write(newcode)
                        break
                    except Exception as e:
                        try_api+=1
                        logger.error("Error in api.api_gpt, retrying...")
                        logger.error(str(e))     

                history.append({
                    "iteration": i,
                    "suspiciousCodeLines": suspiciousCodeLines,
                    "codepath": target,
                    "fix": fix,
                    "score": score
                })
            else: #correct
                if(i==0):
                    logger.info("Finish in mismatch with {} iterations.".format(max_i))
                else:
                    logger.info("Finish in suspiciousline with {} iterations.".format(i))    
                FileUtils.removeDirContent(Config.WORK_DIR)
                end_time= time.time()
                total_time = end_time - start_time
                suspicious_time = total_time - preprocess_time
                return 1,preprocess_time,suspicious_time
            FileUtils.removeDirContent(Config.WORK_DIR)
        except func_timeout.exceptions.FunctionTimedOut:
            logger.error("Suspiciousline repair timeout.")
        except Exception as e:
            logger.error("Suspiciousline exception.")
            logger.error(str(e))
            if(i==0):
                logger.error("Suspiciousline repair error.")
            else:
                logger.error("Bad fix. Roll back to the previous version.")
                with open(patch_dir/f"{src.split('.')[0]}_{i-1}.v", 'r') as back: #rollback to the previous version
                    with open(Path("".join(bugInfo["src_file"])), 'w') as codepath:
                        backup = back.read()
                        codepath.write(backup)
    end_time= time.time()
    total_time = end_time - start_time
    suspicious_time = total_time - preprocess_time
    return 0,preprocess_time,suspicious_time

def testAll(logger, benchmarkArg, max_i):
    benchmark = BenchmarkFactory.createBenchmark(benchmarkArg)
    allBugs = benchmark.getAllBugs()
    for project, version in allBugs:
        try:
            bugInfo = benchmark.getBugInfo(project, version)
            logger.info("////////Start Repair {} {}.////////".format(project, version))
            startTime = time.time()
            history = []

            preprocess_time = 0
            mismatch_time = 0
            suspicious_time = 0


            working_dir = Path(bugInfo["proj_dir"])

            nerr,preprocess_time,mismatch_time = test_mismatch(logger, benchmark, bugInfo, working_dir, max_i)

            if nerr==0:
                nerr,preprocess_time2,suspicious_time =test_suspiciousline(logger, benchmark, bugInfo, working_dir, history, max_i)
                preprocess_time += preprocess_time2
                if nerr==0:
                    logger.info("FIX ERROR.")

            endTime = time.time()
            logger.info("Preprocess Time: {}s.".format(preprocess_time))
            logger.info("Mismatch Time: {}s.".format(mismatch_time))
            logger.info("Suspicious Time: {}s.".format(suspicious_time))
            logger.info("Total Time: {}s.".format(endTime-startTime))
            FileUtils.removeDirContent(Config.WORK_DIR)
        except func_timeout.exceptions.FunctionTimedOut:
            logger.error("{}_{} Repair timeout.".format(project, version))
        except Exception as e:
            logger.error("{}_{} Repair error.".format(project, version))
            logger.error(str(e))

if __name__ == "__main__":
    # Max iterations
    max_i=4
    # Check fix succeed
    nerr=0
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-b", "--benchmark", help="Project")
    aparser.add_argument("-p", "--project", help="Project")
    aparser.add_argument("-v", "--version", help="Bug Id")
    logger = Logger.initLogger(Config.LOG_PATH)
    
    args = aparser.parse_args()
    logger.info(args)
    if args.benchmark == None:
        logger.error("No benchmark.")
        sys.exit(0)
    if args.project == None and args.version == None:
        testAll(logger, args.benchmark, max_i)
    else:
        if args.project == None:
            logger.error("No project.")
            sys.exit(0)
        if args.version == None:
            logger.error("No bug id.")
            sys.exit(0)
        history = []

        benchmark = BenchmarkFactory.createBenchmark(args.benchmark)

        bugInfo = benchmark.getBugInfo(args.project, args.version)

        working_dir = Path(bugInfo["proj_dir"])

        nerr,preprocess_time,mismatch_time = test_mismatch(logger, benchmark, bugInfo, working_dir, max_i)
        if nerr==0:
            nerr,preprocess_time2,suspicious_time = test_suspiciousline(logger, benchmark, bugInfo, working_dir, history, max_i)
            if nerr==0:
                logger.info("FIX ERROR.")

