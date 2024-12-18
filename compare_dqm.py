
import ROOT

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('DQM', type = ROOT.TFile.Open)
parser.add_argument('simple', type = ROOT.TFile.Open)

args = parser.parse_args()

DQMDir = args.DQM.Get('DQMData/Run 1/HLT/Run summary/Tracking/ValidationWRTtp')

DQMInfo = {
    'rt': DQMDir.num_reco_coll.GetBinContent(1),
    'at': DQMDir.Get('num_assoc(recoToSim)_coll').GetBinContent(1),
    'ast': DQMDir.Get('num_assoc(simToReco)_coll').GetBinContent(1),
    'dt': DQMDir.num_duplicate_coll.GetBinContent(1),
    'st': DQMDir.num_simul_coll.GetBinContent(1),
}

next(iter(args.simple.simpleValidation0.output))

simpleInfo = {
    'rt': args.simple.simpleValidation0.output.rt,
    'at': args.simple.simpleValidation0.output.at,
    'ast': args.simple.simpleValidation0.output.ast,
    'dt': args.simple.simpleValidation0.output.dt,
    'st': args.simple.simpleValidation0.output.st,
}

for key in DQMInfo:
    print(key, int(DQMInfo[key]), simpleInfo[key])

