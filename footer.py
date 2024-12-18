
from utils import expand_process
process = expand_process(process,inputs,params,tune,chain,target, associator_task)
process.TFileService = cms.Service('TFileService', fileName=cms.string(options.outputFile)
                                   if cms.string(options.outputFile) else 'default.root')

print("Saving results in file", process.TFileService.fileName)
                                   
with open('process_to_run_dump.py', 'w') as new:
    new.write(process.dumpPython())
