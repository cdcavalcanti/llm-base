#!/usr/bin/env bash
# Ciclo 0 da LLM própria. Roda no servidor da GPU. Não treina e não baixa peso.
set -u
echo "=== nvidia-smi ==="
nvidia-smi
echo "=== memoria da placa ==="
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free --format=csv
echo "=== driver e compute ==="
nvidia-smi --query-gpu=index,driver_version,compute_cap --format=csv
echo "=== processos na GPU ==="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo "=== ram ==="
free -h
echo "=== disco ==="
df -h
