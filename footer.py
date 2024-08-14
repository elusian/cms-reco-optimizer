
from utils import expand_process
process = expand_process(process,inputs,params,tune,chain,target)
process.TFileService = cms.Service('TFileService', fileName=cms.string(options.outputFile)
                                   if cms.string(options.outputFile) else 'default.root')
                                   
with open('process_to_run_dump.py', 'w') as new:
    new.write(process.dumpPython())
