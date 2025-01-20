import FWCore.ParameterSet.Config as cms

def customize_tracking_with_retune(process):
    # Target the specific module type
    target_module_name = "hltPixelTracksSoA"

    # Check if the target module exists in the process
    if hasattr(process, target_module_name):
        module = getattr(process, target_module_name)

        # Update parameters directly
        module.CAThetaCutBarrel = cms.double(0.00111685053)
        module.CAThetaCutForward = cms.double(0.00249872683)
        module.hardCurvCut =  cms.double(0.695091509)
        module.dcaCutInnerTriplet = cms.double(0.0419242041)
        module.dcaCutOuterTriplet = cms.double(0.293522194)

        # Modify vector parameters
        module.phiCuts = cms.vint32(
            832, 379, 481, 765, 1136,
            706, 656, 407, 1212, 404,
            699, 470, 652, 621, 1017,
            616, 450, 555, 572
        )
    return process
