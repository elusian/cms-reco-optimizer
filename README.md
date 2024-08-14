<img width="1144" alt="Screenshot 2023-11-24 alle 09 46 27" src="https://github.com/cms-pixel-autotuning/CA-parameter-tuning/assets/16901146/5bee2244-9afc-46a2-99c6-a75705045442">


This repo has a new `optimize_reco.py` script, modelled on top of `optimize.py`, thought to make the MOPSO work with a generic `cms-sw` reconstruction config in input. Given a list of modules we want to tune, a target we want to validate, and the parameters to tune, it automaically builds a `cmsRun` config derived from the input one that is ready to be run and "tuned" by the MOPSO.

It works like this. Let's say we have a `step3_pixel.py` config that runs pixel tracking RECO (+VALIDATION). Could be the one generated with

``` 
cmsDriver.py step3 -s RAW2DIGI:RawToDigi_pixelOnly,RECO:reconstruction_pixelTrackingOnly,VALIDATION:@pixelTrackingOnlyValidation,DQM:@pixelTrackingOnlyDQM --conditions auto:phase1_2023_realistic --datatier GEN-SIM-RECO,MINIAODSIM,NANOAODSIM,DQMIO -n 10 --eventcontent RECOSIM,MINIAODSIM,NANOEDMAODSIM,DQM --geometry DB:Extended --era Run3_2023 --procModifiers pixelNtupletFit,gpu --filein file:step2.root --fileout file:step3.root --no_exec --python_filename step3_pixel.py
```

Then one can launch the `optimize_reco.py` with something like:

```
./optimize_reco.py step3_pixel.py -t pixelTracksCUDA -v pixelTracks --pars phiCuts z0Cut -f file:/data/user/adiflori/ttbar_2023/2023D/00930c1c-4923-410a-8394-a0eea37a4114.root -p 100 -i 100 -b 2 2
```

going through the options:

- `-t\--tune` gets the name of the module we want to tune (this could be a list but for the moment implemented only for a single module)
- `-v\--validate` is the modules that produces the object on which we want to validate, given in input to the validation.
- `--pars` gets the list of parameters that we want to tune with the MOPSO. This could be either a list of parameters, either an input text file with each parameter comma (`,`) separated.
- `-f` to specify the list of files to be used in input.
- `-p\--num_particles` the number of agents.
- `-i\--num_iterations` the number of iterations.
- `-b\--bounds` takes care of the definition of the upper and lower bounds for the parameters. These can be parsed in two ways: 
    1. as scaling factors w.r.t. the default parameters found in the config. In this case the syntax is `-b m M` where the first define the lower bounds as `default_values / m` and the second the upper ones as `default_values * M`.
    2. As input `json` file containing the dictionary for the bounds. Such as, for this case, `{"z0Cuts":12, "phiCuts": [400,400,400,400,400]}`. Note that the options may be mixed, e.g. `-b 3 max.json`.
    

Launching this the `optimize_reco.py` will run the following steps:

1. loads the `process` defined in the input config adding to it the `DependencyGraph` `Service` and setting it to run with no source (`EmptySource`) and zero events. The new `process_zero` is then run just to get the graph of the modules used in the config.

2. given the graphs it gets all the modules that are need to go from the module(s) `tune` to the module `validate`.

3. define the upper and lower bounds (`ub`/`lb`) that will be parsed to the MOPSO object. 

4. write a new `process_to_run.py` config that is modified in order to get the results of the previous steps and to be able to get the needed params in input from a csv file (the output of the MOPSO basically). This is done by prepending `header.py` and appending  `footer.py`. 

5. the new config takes in input also the number of threads (`--num_thrads`), events (`--num_events`) and the input files.

Then, the `process_to_run.py` is the config actually run by the MOPSO and it uses the results from the `optimize_reco.py` to build the `num_particles` different chains to go from (i-th) module(s) `tune` to the (i-th) module `validate` taking care of the tasks definition, of rewriting all the inputs and defining the final validation step (removing the possible output steps).

All of this happens in an ad-hoc folder and one may continue the previous run by specifing in which folder (`--dir`) the script should look for the previous end state and for how many extra iterations `--continuing`. E.g.

```
./optimize_reco.py --continuing 10 --dir optimize.step3_pixel_20231123.010104
```

For the moment I'm opening it here to make it available. But I would like to include this in `The-Optimizer` examples folder. 


TODOs for the future (will go in an issue):

- check if the "prevalidation" modules are in the config or not. If not add them. At the moment we rely on the fact that they are anyway defined somewhere;
- at the moment this work only with tracking reconstruction given we have the target validation module. The `hgcal` option to be added;
- move all the methods for the information extraction in a single general class;
- finalize the `--timing` option to add throughput/timing calculations for each run;
- add automatic plotting and MTV running;
- allow for more modules to tune in input.
