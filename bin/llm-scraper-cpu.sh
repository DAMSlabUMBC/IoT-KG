#!/bin/bash

#SBATCH --cluster=chip-cpu
#SBATCH --partition=general
#SBATCH --job-name=llm-scraper              # Job name to appear in the SLURM queue
#SBATCH --array=1-25                       # Run array tasks 0..999 (i.e. 1000 tasks)
#SBATCH --mail-user=gsantos2@umbc.edu       # Email for job notifications (replace with your email)
#SBATCH --mail-type=END,FAIL                # Notify on job completion or failure
#SBATCH --mem=16GB                        # Memory allocation in MB (150 GB)
#SBATCH --time=24:00:00                     # Maximum runtime for the job (70 hours)
#SBATCH --qos=medium
#SBATCH --output=llm-scraper_output/llm-scraper_%A_%a.out       # Output log (include %A for job ID, %a for array index)
#SBATCH --error=llm-scraper_error/llm-scraper_%A_%a.err        # Error log

echo "SLURM job started at $(date)"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"

# activate conda environment
conda init
source ~/.bashrc
conda activate test_env2
pip list | grep playwright

conda list

sleep 10 # Wait 10 seconds to ensure conda environment has been activated

# Set a unique port for this array task
PORT="$((11434 + SLURM_ARRAY_TASK_ID))"
export PORT

# sets playwright
export PLAYWRIGHT_BROWSERS_PATH=/umbc/ada/ryus/users/gsantos2/tools/playwright_browsers
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

# Checking Python version
python --version

sleep 10

# Use python to run queries
python main.py \
  --config_file="best_buy_config.json" \
  --batch_file="bestbuy_batches/batch_${SLURM_ARRAY_TASK_ID}.txt" \
  --output_file="bestbuy_extracted/extracted_${SLURM_ARRAY_TASK_ID}.txt" \
  --ollama_port="${PORT}"

echo "Python script done for task ${SLURM_ARRAY_TASK_ID}."

echo "SLURM job completed at $(date)"

