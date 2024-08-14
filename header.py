from FWCore.ParameterSet.VarParsing import VarParsing
from utils import read_csv
# VarParsing instance
options = VarParsing('analysis')
# Custom options
options.register('parametersFile',
              'default/default_params.csv',
              VarParsing.multiplicity.singleton,
              VarParsing.varType.string,
              'Name of parameters file')
options.parseArguments()
inputs = read_csv(options.parametersFile)
