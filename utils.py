import numpy as np
from inspect import getmro
import sys
import os
import warnings
from itertools import cycle

spinner = cycle('-/|\\')

def spinning(): ##doesn't work
    print(next(spinner),flush=True,end="")
    os.sleep(0.05)
    sys.stdout.write("\r")

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    import imp

try:
    from FWCore.ParameterSet.Mixins import _Parameterizable, _ValidatingParameterListBase
    import FWCore.ParameterSet.Config as cms
    from FWCore.ParameterSet.MassReplace import MassSearchReplaceAnyInputTagVisitor
    from HLTrigger.Configuration.common import modules_by_type
except:
    print("Working without CMS modules")

# calculate the metrics from validation results
def get_metrics(uproot_file, id, regions = ['global', 'displaced', 'lowpt'], raw = False):
    tree = uproot_file['simpleValidation' + str(id)]['output']

    metrics = []
    for region in regions:
        total_rec = tree[region + '_rt'].array()[0]
        total_ass = tree[region + '_at'].array()[0]
        total_ass_sim = tree[region + '_ast'].array()[0]
        total_dup = tree[region + '_dt'].array()[0]
        total_sim = tree[region + '_st'].array()[0]

        #print(f'{id}:', total_rec, total_ass, total_sim, total_ass_sim, total_dup)

        if total_ass == 0 or total_rec == 0 or total_sim == 0 or total_ass_sim == 0:
            metrics.append( [1.0] * 2)
        else:
            metrics.append([1 - total_ass_sim / total_sim, (total_rec - total_ass + total_dup) / total_rec])

    metrics = np.array(metrics)

    return metrics

# read a csv file, return a matrix
def read_csv(filename):
    matrix = np.genfromtxt(filename, delimiter=",", dtype=float)
    if matrix.ndim == 2:
        return matrix
    else:
        return np.array([matrix])
    
# write a matrix to a csv file
def write_csv(filename, matrix):
    np.savetxt(filename, matrix, fmt='%.18f', delimiter=',')

### cmsRun specific helpers

def parseProcess(filename): 
  # from https://github.com/cms-patatrack/patatrack-scripts/blob/master/multirun.py
  # parse the given configuration file and return the `process` object it define
  # the import logic is taken from edmConfigDump
  try:
    handle = open(filename, 'r')
  except:
    print("Failed to open %s: %s" % (filename, sys.exc_info()[1]))
    sys.exit(1)

  # make the behaviour consistent with 'cmsRun file.py'
  sys.path.append(os.getcwd())
  try:
    pycfg = imp.load_source('pycfg', filename, handle)
    process = pycfg.process
  except:
    print("Failed to parse %s: %s" % (filename, sys.exc_info()[1]))
    sys.exit(1)

  handle.close()
  return process

def has_params(typ):
    return _Parameterizable in getmro(typ)

def is_v_input(typ):
    return _ValidatingParameterListBase in getmro(typ)

def chain_update(process,inputs,tune,modules):

    taskList = []
    for i,_ in enumerate(inputs):
        
        replace = {}
        # define replacers for all
        for f in modules + tune:
            replace[f] = MassSearchReplaceAnyInputTagVisitor(f, f+str(i), verbose=False) # True to see all the renamings
            # create new ith module
            if f not in tune: #we have already taken care of the modules to tune
                setattr(process, f + str(i), getattr(process,f).clone()) 

        #apply replacement for all the ith modules, with all the (other) ith modules
        for m in modules:
            module = getattr(process,m + str(i))
            for f in modules + tune:
                if f != m: # not realy needed
                    replace[f].doIt(module, m + str(i))
            taskList.append(module)

        for t in tune:
            taskList.append(getattr(process,t + str(i)))
            
    process.mainTask = cms.Task(*taskList)
    process.mainPath = cms.Path(process.mainTask)

    process.schedule.extend([process.mainPath])
    return process

def remove_outputs(process):

    for s in process.endpaths_():#.keys():   
        process.schedule.remove(getattr(process,s))

    return process

def add_validation(process,inputs,target, task = None):

    # Here we assume that the process we have given in input has already the 
    # validation and the prevalidation well defined and so we just track
    # back wich hit associator we need to use

    hitassoc = ""
    for f in modules_by_type(process,"TrackAssociatorEDProducer"):
        #print(getattr(f,"label_tr"))
        if getattr(f,"label_tr").value() == target:
            hitassoc = getattr(f,"associator").value()
            break

    print('Found associator', hitassoc)
    
    taskList = []
    for i,_ in enumerate(inputs):
        
        # All these params may be copied from the MTV defined in the process
        name = 'simpleValidation' + str(i)
        setattr(process, name, cms.EDAnalyzer('LessSimpleValidation',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhiTP = cms.double(3.2),
                maxRapidityTP = cms.double(3),#(2.5),
                minHitTP = cms.int32(0),
                minPhiTP = cms.double(-3.2),
                minRapidityTP = cms.double(-3),#(-2.5),
                pdgIdTP = cms.vint32(),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.9),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(60),#(3.5),
                regions = cms.VPSet(
                    cms.PSet(label = cms.string('global')),
                    cms.PSet(label = cms.string('displaced'), minTip = cms.double(0.1)),
                    cms.PSet(label = cms.string('lowpt'), maxPt = cms.double(5))
                ),
                trackLabels = cms.VInputTag(target + str(i)),
                trackAssociator = cms.untracked.InputTag(hitassoc),
                trackingParticles = cms.InputTag('mix', 'MergedTrackTruth')
            )
        )

        taskList.append(getattr(process, name))

    process.simpleValidationSeq = cms.Sequence(sum(taskList[1:],taskList[0])) if task is None else cms.Sequence(sum(taskList[1:],taskList[0]), task)
    process.simpleValidationPath = cms.EndPath(process.simpleValidationSeq)
    process.schedule.extend([process.simpleValidationPath])

    return process
    
def modules_tuning(process,inputs,params,tune):
    
    for i, row in enumerate(inputs):
        # print("Param row", i, "is", row)
        modules_to_tune = [getattr(process,t).clone() for t in tune]
        enum_p = iter(enumerate(params))
        n = 0
        for p in params:
            # print("Setting parameter", p)
            for name, m in zip(tune,modules_to_tune):
                # print("For module", name)
                this_params = m.parameters_()
                if p in this_params:
                    par = this_params[p]
                    # print("Standard param is", par)
                    if is_v_input(type(par)):
                        l = len(par.value())
                        setattr(m,p,[int(row[n+i]) for i in range(l)])
                        # print("Setting to", [int(row[n+i]) for i in range(l)])
                    else:
                        l = 1
                        setattr(m,p,row[n])
                        # print("Setting to", row[n])
            n = n + l
        for n,m in zip(tune,modules_to_tune):
            setattr(process,n+str(i),m)
        
    return process
   
def expand_process(process,inputs,params,tune,chain,target, task):
    
    process = remove_outputs(process) #check for all EndPaths
    process = modules_tuning(process,inputs,params,tune)
    process = add_validation(process,inputs,target, task)
    process = chain_update(process,inputs,tune,chain+[target])
    

    return process
            
