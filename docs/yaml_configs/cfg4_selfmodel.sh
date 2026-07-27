#!/bin/bash

# --- 帮助信息 ---
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --nnodes N              设置节点数量 (默认: 根据环境变量或1)"
    echo "  --nproc-per-node N      设置每个节点的GPU数量 (默认: 根据环境变量或8)"
    echo "  --master-addr ADDR      设置主节点地址 (默认: 根据环境变量或localhost)"
    echo "  --master-port PORT      设置主节点端口 (默认: 根据环境变量或29500)"
    echo "  --node-rank N           设置节点等级 (默认: 根据环境变量或0)"
    echo "  --batch-size N          设置每GPU批次大小 (默认: 8)"
    echo "  --help, -h              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                           # 使用自动检测的配置"
    echo "  $0 --nnodes 2 --nproc-per-node 4           # 手动指定2节点，每节点4GPU"
    echo "  $0 --master-addr 192.168.1.100 --master-port 12345  # 手动指定主节点"
}

# --- 解析命令行参数 ---
OVERRIDE_NNODES=""
OVERRIDE_NPROC_PER_NODE=""
OVERRIDE_MASTER_ADDR=""
OVERRIDE_MASTER_PORT=""
OVERRIDE_NODE_RANK=""
OVERRIDE_BATCH_SIZE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --nnodes)
            OVERRIDE_NNODES="$2"
            shift 2
            ;;
        --nproc-per-node)
            OVERRIDE_NPROC_PER_NODE="$2"
            shift 2
            ;;
        --master-addr)
            OVERRIDE_MASTER_ADDR="$2"
            shift 2
            ;;
        --master-port)
            OVERRIDE_MASTER_PORT="$2"
            shift 2
            ;;
        --node-rank)
            OVERRIDE_NODE_RANK="$2"
            shift 2
            ;;
        --batch-size)
            OVERRIDE_BATCH_SIZE="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# --- NCCL ---
echo "--- DDP Training (v2) ---"
echo "策略: DDP (DistributedDataParallel)"
echo "目标: 解决1B模型通信瓶颈"


# --- NVIDIA ---
# export NVIDIA_TF32_OVERRIDE=1

# --- 多机多卡配置检测与设置 ---
echo "检测云平台多机多卡环境变量..."
echo "MLP_WORKER_0_HOST: $MLP_WORKER_0_HOST"
echo "MLP_WORKER_0_PORT: $MLP_WORKER_0_PORT"
echo "MLP_WORKER_NUM: $MLP_WORKER_NUM"
echo "MLP_WORKER_GPU: $MLP_WORKER_GPU"
echo "MLP_ROLE_INDEX: $MLP_ROLE_INDEX"

# 检查是否存在云平台环境变量，如果存在则使用，否则使用默认的单机配置
if [[ -n "$MLP_WORKER_0_HOST" && -n "$MLP_WORKER_0_PORT" && -n "$MLP_WORKER_NUM" && -n "$MLP_WORKER_GPU" ]]; then
    echo "检测到云平台多机多卡环境，使用云平台配置..."
    # 云平台多机多卡配置
    NNODES=$MLP_WORKER_NUM                    # 节点数量
    NPROC_PER_NODE=$MLP_WORKER_GPU           # 每个节点的GPU数量
    MASTER_ADDR=$MLP_WORKER_0_HOST           # 主节点地址
    MASTER_PORT=$MLP_WORKER_0_PORT           # 主节点端口
    # 根据云平台GPU数量设置可见设备
    if [[ $MLP_WORKER_GPU -eq 8 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
    elif [[ $MLP_WORKER_GPU -eq 4 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1,2,3
    elif [[ $MLP_WORKER_GPU -eq 2 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1
    elif [[ $MLP_WORKER_GPU -eq 1 ]]; then
        export CUDA_VISIBLE_DEVICES=0
    else
        # 自动生成CUDA_VISIBLE_DEVICES
        CUDA_DEVICES=""
        for ((i=0; i<$MLP_WORKER_GPU; i++)); do
            if [[ $i -eq 0 ]]; then
                CUDA_DEVICES="$i"
            else
                CUDA_DEVICES="$CUDA_DEVICES,$i"
            fi
        done
        export CUDA_VISIBLE_DEVICES=$CUDA_DEVICES
    fi
    echo "使用云平台多机多卡配置"
else
    echo "未检测到云平台环境变量，使用默认单机配置..."
    # 默认单机多卡配置
    NNODES=1                                  # 单机
    NPROC_PER_NODE=2                         # 8张GPU
    MASTER_ADDR='localhost'                   # 本地地址
    MASTER_PORT='29334'                      # 默认端口
    export CUDA_VISIBLE_DEVICES=6,7  # 8张GPU
    echo "使用默认单机多卡配置"
fi

# --- 设置节点等级 (node rank) ---
# 默认为0 (主节点)，多机训练时云平台会提供MLP_ROLE_INDEX
if [[ -n "$MLP_ROLE_INDEX" ]]; then
    NODE_RANK=$MLP_ROLE_INDEX
else
    NODE_RANK=0  # 默认为主节点
fi

# --- 应用命令行参数覆盖 ---
if [[ -n "$OVERRIDE_NNODES" ]]; then
    NNODES=$OVERRIDE_NNODES
    echo "命令行覆盖 NNODES: $NNODES"
fi

if [[ -n "$OVERRIDE_NPROC_PER_NODE" ]]; then
    NPROC_PER_NODE=$OVERRIDE_NPROC_PER_NODE
    echo "命令行覆盖 NPROC_PER_NODE: $NPROC_PER_NODE"
    # 重新设置CUDA_VISIBLE_DEVICES
    if [[ $NPROC_PER_NODE -eq 8 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
    elif [[ $NPROC_PER_NODE -eq 4 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1,2,3
    elif [[ $NPROC_PER_NODE -eq 2 ]]; then
        export CUDA_VISIBLE_DEVICES=0,1
    elif [[ $NPROC_PER_NODE -eq 1 ]]; then
        export CUDA_VISIBLE_DEVICES=0
    else
        # 自动生成CUDA_VISIBLE_DEVICES
        CUDA_DEVICES=""
        for ((i=0; i<$NPROC_PER_NODE; i++)); do
            if [[ $i -eq 0 ]]; then
                CUDA_DEVICES="$i"
            else
                CUDA_DEVICES="$CUDA_DEVICES,$i"
            fi
        done
        export CUDA_VISIBLE_DEVICES=$CUDA_DEVICES
    fi
fi

if [[ -n "$OVERRIDE_MASTER_ADDR" ]]; then
    MASTER_ADDR=$OVERRIDE_MASTER_ADDR
    echo "命令行覆盖 MASTER_ADDR: $MASTER_ADDR"
fi

if [[ -n "$OVERRIDE_MASTER_PORT" ]]; then
    MASTER_PORT=$OVERRIDE_MASTER_PORT
    echo "命令行覆盖 MASTER_PORT: $MASTER_PORT"
fi

if [[ -n "$OVERRIDE_NODE_RANK" ]]; then
    NODE_RANK=$OVERRIDE_NODE_RANK
    echo "命令行覆盖 NODE_RANK: $NODE_RANK"
fi

# --- Environment/Paths ---
export XDG_CACHE_HOME=/mnt/vepfs01/output/junliang/cache/
export HF_HOME=/mnt/vepfs01/output/junliang/cache


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/../../../../")
echo "PROJECT_ROOT: $PROJECT_ROOT"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
export PYTHONPATH="${PROJECT_ROOT}/thirdparty:${PROJECT_ROOT}/thirdparty/overmind:${PROJECT_ROOT}/mozrobot/src:${PROJECT_ROOT}/capturex/src:${PYTHONPATH}"

export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_OFFLINE=1

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=1   

# --- Training Parameters ---
# NNODES=1
TASK=InsertPour_finetune_lr25_5e_6_gpu16
POLICY=spirit_qwen_dit_cotrain
# LOADCKPT=/mnt/vepfs01/output/lmz/codebase/mozbrain_train_0320/outputs/train_posttrain_fsdp2_0324/checkpoints/070000/pretrained_model/model.safetensors
# LOADCKPT=/mnt/vepfs01/output/lmz/checkpoint/qwen_4b_posttrain_0324_7w/model.safetensors
LOADCKPT=/mnt/vepfs01/output/fanbohao/model_ckpts/pretrained_model/model.safetensors
OFFLINE_STEPS=50000
EVAL_FREQ=2500
BATCH_SIZE_PER_GPU=32
GLOBAL_BATCH_SIZE=$(($BATCH_SIZE_PER_GPU * $NPROC_PER_NODE * $NNODES))
EVAL_BATCH_SIZE=32
SAVE_FREQ=10000
LOG_FREQ=100
timestamp=$(date +%Y%m%d_%H%M%S)
JOB_NAME=${TASK}
REPO_ID=$TASK
DATAPATH=/mnt/vepfs01/output/yifeng/resources/frontdesk/
# tos://ai-dev/moz-datasets/pretrain-v2/
SAMPLEWEIGHT=/mnt/vepfs01/output/yifeng/resources/frontdesk/20260510_InsertPenFlower_train.json
MMSAMPLEWEIGHT=N/A
REPO_ID_EVAL=$TASK-eval
EVALRBWEIGHT=/mnt/vepfs01/output/yifeng/resources/frontdesk/20260510_InsertPenFlower_val.json
# /mnt/vepfs01/output/juntu/FrontDesk/0_data/0331/eval.json
EVALMMWEIGHT=N/A
USE_WANDB=true
NUM_WORKER=$(($NNODES * $NPROC_PER_NODE * 4))
NUM_STATS_SAMPLE=1000000
EVAL_SAMPLE_INTERVAL=1
# OFFLINE_STATS_PATH=/mnt/vepfs01/output/juntu/FrontDesk/0_data/0331/norm_stats.json
MASK_Z=true ###########################################################


WARMPUP_STEPS=1000
# 学习率在第 20000 步衰减到 decay_lr (= peak_lr 的 1/5)，之后保持 decay_lr 不变
DECAY_STEPS=$((20000 - WARMPUP_STEPS))


export WANDB_BASE_URL=https://api.bandw.top
export WANDB_API_KEY=6fc02fe00080833953275e2242f06dbd6c512f33 # JTZhao's WandB Key

######################################################################################################################## Debug 时请使用
# debug only
# NPROC_PER_NODE=1                            # 1张GPU
# export CUDA_VISIBLE_DEVICES=4,5,6,7 # 1张GPU
# export BATCH_SIZE_PER_GPU=4
# export NUM_WORKERS_PER_GPU=0 
# export NUM_WORKERS=$((NPROC_PER_NODE * NUM_WORKERS_PER_GPU))
# export OMP_NUM_THREADS=1
# NUM_WORKER=0
# EVAL_FREQ=5
# SAVE_FREQ=100
# USE_WANDB=false
# LOG_FREQ=1
# NUM_STATS_SAMPLE=100
# EVAL_BATCH_SIZE=4
# LOADCKPT=null

# SAMPLEWEIGHT=/mnt/vepfs01/output/juntu/FrontDesk/0_data/0331/processing/debug_train.json
# MMSAMPLEWEIGHT=N/A
# EVALRBWEIGHT=/mnt/vepfs01/output/juntu/FrontDesk/0_data/0331/processing/debug_eval.json
# EVALMMWEIGHT=N/A
######################################################################################################################## Debug 时请使用

echo "--- FSDP Training with Activation Checkpointing ---"
echo "NNODES: $NNODES"
echo "NPROC_PER_NODE: $NPROC_PER_NODE"
echo "MASTER_ADDR: $MASTER_ADDR"
echo "MASTER_PORT: $MASTER_PORT"
echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "BATCH_SIZE_PER_GPU: $BATCH_SIZE_PER_GPU"
echo "GLOBAL_BATCH_SIZE: $GLOBAL_BATCH_SIZE"
echo "JOB_NAME: $JOB_NAME"
echo "---------------------"

# --- Launch Training ---
torchrun \
    --nnodes $NNODES \
    --nproc_per_node $NPROC_PER_NODE \
    --master_addr $MASTER_ADDR \
    --master_port $MASTER_PORT \
    --node_rank $NODE_RANK  \
    --rdzv_backend=static \
    ${PROJECT_ROOT}/lerobot/scripts/train_posttrain_fsdp2.py \
    --seed=64 \
    --policy.type=$POLICY \
    --policy.observation_config.moz1_structure=wholebody_without_base \
    --dataset.repo_id=$REPO_ID \
    --dataset.root=$DATAPATH \
    --wandb.enable=true \
    --job_name=$JOB_NAME \
    --eval_freq=$EVAL_FREQ \
    --batch_size=$BATCH_SIZE_PER_GPU \
    --steps=$OFFLINE_STEPS \
    --policy.scheduler_warmup_steps=$WARMPUP_STEPS \
    --policy.scheduler_decay_steps=$DECAY_STEPS \
    --save_freq=$SAVE_FREQ \
    --log_freq=$LOG_FREQ \
    --wandb.project="SKEW_FRUITS_SPIRIT_VLA" \
    --output_dir=${PROJECT_ROOT}/outputs/$JOB_NAME \
    --dataset.sample_weights_cfg=$SAMPLEWEIGHT \
    --dataset.use_mozdataset=false \
    --dataset.image_transforms.use_posttrain_transform=true \
    --dataset.image_transforms.image_size="[240,320]" \
    --policy.observation_config.image_size="[240,320]" \
    --policy.backbone=Qwen/Qwen3-VL-4B-Instruct \
    --num_workers=$NUM_WORKER \
    --pretrained_ckpt_path=$LOADCKPT \
    --pretrained_load_norm=false \
    --dataset.disable_stats=false \
    --use_raw_dataset=true \
    --dataset.num_stats_samples=$NUM_STATS_SAMPLE \
    --dataset.use_stats_cache=true \
    --policy.use_state=true \
    --policy.mask_z=$MASK_Z \
    --policy.use_separate_lr=false \
    --policy.optimizer_weight_decay=1e-2 \
    --policy.scheduler_decay_lr=5e-6 \
    --policy.optimizer_lr=2.5e-5 \
    --policy.observation_config.robot_type=moz1 \
    --policy.observation_config.use_gripper_action=true \
    --policy.attention_implementation=flash_attention_2 \
    --policy.dit_hidden_size=1536 \
    --policy.dit_num_heads=32 \
    --policy.dit_num_layers=16 \
    --policy.dit_interleave_self_attention=true \
    --policy.dit_cross_attention_dim=2560 \
    --policy.dit_dropout=0.2 \
    --policy.enable_packing=true \
    --enable_mfu=true \
    --policy.vlm_use_sac=true \
    --policy.vlm_sac_skip_last_n_layers=8 \
    --fsdp2_param_bf16=true \
    --policy.rb_preprocess_mode=dataloader \
    --policy.qwen3_expert_hidden_size=1024 \
    --policy.qwen3_expert_num_layers=18 \
    --policy.qwen3_expert_num_heads=32 \
    --policy.qwen3_expert_num_kv_heads=8 \
    --policy.qwen3_expert_head_dim=128 \
    --policy.qwen3_expert_intermediate_size=4096 \
    --policy.qwen3_expert_rms_norm_eps=1e-6 \
    --policy.qwen3_expert_rope_theta=5000000.0 \
    --policy.qwen3_expert_dropout=0.0 \
    --policy.qwen3_expert_interleave_self_attention=true \
    --policy.qwen3_expert_gating_mode=headwise \
    --policy.qwen3_expert_fusion_mode=cross_attention \
    --policy.qwen3_expert_num_vlm_last_embd=1 \
    --policy.enable_action_token=false \
    --policy.enable_dit=true \
    --policy.action_expert_type=qwen3_gate \
    # --eval_batch_size=$EVAL_BATCH_SIZE \
    # --eval_dataset.repo_id=$REPO_ID_EVAL \
    # --eval_dataset.sample_weights_cfg=$EVALRBWEIGHT \
    # --eval_dataset.root=$DATAPATH \
    # --eval_dataset.use_mozdataset=false \
    # --eval_dataset.image_transforms.use_posttrain_transform=true \
    # --eval_dataset.image_transforms.image_size="[240,320]" \
    # --eval_dataset.sample_interval=$EVAL_SAMPLE_INTERVAL \
    # --eval_dataset.scaling_law=false \

    # --dataset.load_norm_stats_json=$OFFLINE_STATS_PATH \
# 使用 eval
# --eval_batch_size=$EVAL_BATCH_SIZE \
#     --eval_dataset.repo_id=$REPO_ID_EVAL \
#     --eval_dataset.sample_weights_cfg=$EVALRBWEIGHT \
#     --eval_dataset.multimodal_weights_cfg=$EVALMMWEIGHT \
#     --eval_dataset.root=$DATAPATH \
#     --eval_dataset.use_mozdataset=false \
#     --eval_dataset.image_transforms.use_posttrain_transform=true \
#     --eval_dataset.image_transforms.image_size="[240,320]" \
#     --eval_dataset.sample_interval=$EVAL_SAMPLE_INTERVAL \


# 使用 mm train
# --dataset.multimodal_weights_cfg=$MMSAMPLEWEIGHT \


# recover
#     --recover=true \
#     --recover_checkpoint_dir=xxx \

# 使用 offline 计算好的 norm
#     --dataset.load_norm_stats_json=xxx \
#     --dataset.use_stats_cache=true \

echo "--- Training finished ---"