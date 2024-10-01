
export PYTHONPATH=${PYTHONPATH}:$PWD/The-Optimizer  

cd $CMSSW_BASE/src
cmsenv
git cms-init
git cms-addpkg Validation/RecoTrack
curl https://raw.githubusercontent.com/AdrianoDee/cmssw/6d1a41ac921c5c4f191b7a3d46aabbfa577ee9db/Validation/RecoTrack/plugins/SimpleValidation.cc -o Validation/RecoTrack/plugins/SimpleValidation.cc
scram b -j 12

