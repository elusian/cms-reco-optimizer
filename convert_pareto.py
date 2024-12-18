
from utils import read_csv, get_metrics, write_csv

import optimizer

import uproot

import numpy as np

import os
import subprocess
import itertools

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', type=str, action='store', help = "Directory where to find the pareto front.", required = True)

    args = parser.parse_args()

    os.chdir(args.dir)

    workdir = os.getcwd()
    optimizer.FileManager.working_dir = workdir + "/checkpoint/"
    optimizer.FileManager.loading_enabled = True

    front = read_csv("checkpoint/checkpoint/pareto_front.csv")

    #front = front[:50]

    def split_given_size(a, size):
        return np.split(a, np.arange(size,len(a),size))

    split = split_given_size(front, 100)

    validation_result = 'temp/pareto_front.root'

    population_fitness = []

    default_parameters = read_csv('checkpoint/checkpoint/default.csv')
    with uproot.open('checkpoint/default.root') as uproot_file:
        default_metrics = np.array(get_metrics(uproot_file, 0))

    full_default = np.hstack([default_parameters, np.reshape(default_metrics, (1,6))])

    count = 0
    for subfront in split:
        write_csv('temp/parameters.csv', subfront[:, :-2])
        # redirecting outputs to logs
        logfiles = tuple('%s/logs/%s' % (workdir, name) for name in ['process_convert_out', 'process_convert_err'])
        stdout = open(logfiles[0], 'w')
        stderr = open(logfiles[1], 'w')

        config = 'process_to_run.py'

        num_particles = len(subfront)

        print(f"Running validation on front from {count} to {count + num_particles}")
        count += num_particles

        command = ['cmsRun',config,'parametersFile=temp/parameters.csv', 'outputFile=' + validation_result]
        result = subprocess.run(command,stdout = stdout, stderr = stderr)

        if result.returncode != 0:
            raise RuntimeError("Failed to run validation process")

        with uproot.open(validation_result) as uproot_file:
            population_fitness.extend( [get_metrics(uproot_file, i) for i in range(num_particles)] )

    population_fitness = np.array(population_fitness)

    # print(front)
    # print(population_fitness)

    population_fitness = np.reshape(population_fitness, (population_fitness.shape[0], population_fitness.shape[1]*population_fitness.shape[2]))

    full_fitness = np.hstack([front, population_fitness])
    full_fitness = np.vstack([full_default, full_fitness])
    write_csv('checkpoint/checkpoint/full_pareto_front.csv', full_fitness)


