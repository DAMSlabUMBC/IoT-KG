#!/bin/bash
#------------------------------------------
# MAKE SURE TO RUN THIS SLURM FILE FROM
# WITHIN THE FOLDER THAT CONTAIN THE OUTPUT
# AND ERROR FILES
#------------------------------------------
#SBATCH --cluster chip-gpu
#SBATCH --job-name jupyter 
#SBATCH --gres=gpu:1
#SBATCH --constraint=L40S             # Specific hardware constraint
#SBATCH --nodelist=g24-08
#SBATCH --output=jupyter_output/jupyter-%j.out
#SBATCH --error=jupyter_error/jupyter-%j.err
#SBATCH --time=5:00:00
#SBATCH --mem=16GB

#------------------------------------------
# Uncomment the lines below in order to
#   move any necessary dataset to /scratch
#   Note: you will need to change the
#    commands or use completely new ones
#------------------------------------------
#echo "Moving dataset to local sractch"
#find /directory/to/my/csv/data -name *.csv | awk -v id=${SLURM_JOBID} '{print "cp "$1" /scratch/"id"/."}' | sh


#------------------------------------------
# Uncomment the following lines for to
#   activate a conda environment
#------------------------------------------
#echo "Activating conda environment"
#eval "$(conda shell.bash hook)"
#conda activate <CONDA ENV NAME>


#------------------------------------------
# Get tunneling info
#------------------------------------------
module load Anaconda3
echo "The environment variables are:"
which jupyter-lab
XDG_RUNTIME_DIR=""
node=$(hostname -s)
user=$(whoami)
cluster=chip
port=$(( ( RANDOM % 60000 )  + 1024 ))
#------------------------------------------
# Print tunneling instructions to *.out file
#------------------------------------------
echo "========================================"
echo $PATH
echo -e "
Command to create ssh tunnel below. Run this on your local machine.
ssh -N -f -L ${port}:${node}:${port} ${user}@${cluster}.rs.umbc.edu

Then go to the .err file associated with this SLURM job and copy the
line starting with \"http://127.0.0.1\" into your browser.
"

#------------------------------------------
# Make sure you're using the version of
#   jupyter-lab that you want.
#------------------------------------------
jupyter-lab --no-browser --port=${port} --ip=${node}


# Submit an RT ticket to https://doit.umbc.edu/request-tracker-rt/doit-research-computing/
#  with any questions about this script 
