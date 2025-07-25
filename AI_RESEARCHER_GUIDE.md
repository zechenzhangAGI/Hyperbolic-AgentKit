# AI Researcher Agent Guide

## Overview

The AI Researcher character ("Dr. Nova") is a specialized agent personality designed to help with machine learning research, experiment design, and GPU-accelerated computing tasks.

## Quick Start

1. **Set the character in your `.env` file:**
   ```bash
   CHARACTER_FILE=characters/ai_researcher.json
   ```

2. **Run the agent:**
   ```bash
   poetry run python chatbot.py
   ```

## Character Profile

**Dr. Nova** is an AI Research Scientist with:
- Deep expertise in neural networks and optimization
- Extensive experience with distributed training
- Focus on practical, efficient implementations
- Helpful, methodical approach to problem-solving

## Key Capabilities

### 1. **Experiment Design & Setup**
- Helps design training pipelines
- Recommends model architectures
- Suggests hyperparameter configurations
- Emphasizes reproducible research practices

### 2. **GPU Resource Management**
- Recommends appropriate GPU types for your task
- Can rent GPUs via Hyperbolic integration
- Helps optimize multi-GPU setups
- Monitors resource utilization

### 3. **Remote Development Workflow**
```
You: "I need to train a vision transformer on ImageNet"
Dr. Nova: "I'll help you set that up. Let me first check available GPUs..."
→ Uses `get_available_gpus` to find suitable hardware
→ Uses `rent_compute` to provision GPUs
→ Uses `ssh_connect` to access the machine
→ Uses `remote_write_file` to create training scripts
→ Uses `remote_shell` to launch experiments
→ Uses `remote_read_file` to monitor logs
```

### 4. **Debugging & Optimization**
- Identifies training bottlenecks
- Debugs convergence issues
- Optimizes data loading pipelines
- Fixes CUDA/memory errors

## Example Interactions

### Setting Up a New Experiment
```
You: "I want to fine-tune a BERT model for sentiment analysis"

Dr. Nova will:
1. Discuss dataset and model requirements
2. Recommend GPU configuration (e.g., "A 16GB V100 should suffice")
3. Help rent appropriate compute
4. Create training script with best practices
5. Set up experiment tracking
6. Launch and monitor training
```

### Debugging Training Issues
```
You: "My loss is NaN after 1000 steps"

Dr. Nova will:
1. SSH into your training machine
2. Check training logs for gradient explosions
3. Review your learning rate schedule
4. Suggest gradient clipping or lower learning rates
5. Help implement fixes remotely
```

### Parallel Experiments
```
You: "I need to run hyperparameter search"

Dr. Nova will:
1. Help design the search space
2. Rent multiple GPUs if needed
3. Create parallel experiment scripts
4. Use remote tools to launch all experiments
5. Help aggregate and analyze results
```

## Available Tools

When using the AI Researcher character, these tools are particularly useful:

**GPU Management:**
- `get_available_gpus` - Find suitable hardware
- `rent_compute` - Provision GPU instances
- `terminate_compute` - Clean up resources
- `get_gpu_status` - Monitor active instances

**Remote Development:**
- `ssh_connect` - Access GPU machines
- `remote_shell` - Run commands (training, monitoring)
- `remote_write_file` - Create/modify scripts
- `remote_read_file` - Check logs and outputs
- `remote_list_directory` - Navigate project structure
- `remote_grep` - Search through code/logs
- `remote_replace` - Quick fixes in files

**Other Useful Tools:**
- `web_search` - Find latest papers and techniques
- `DuckDuckGoSearch` - Quick technical queries

## Best Practices

1. **Start Small**: Dr. Nova emphasizes testing on small data first
2. **Track Everything**: Use proper experiment tracking (tensorboard, wandb)
3. **Profile First**: Identify bottlenecks before scaling
4. **Reproducibility**: Always set random seeds and log configurations
5. **Cost-Aware**: Consider compute costs vs. potential gains

## Common Workflows

### 1. **New Project Setup**
```
"Help me set up a new PyTorch project for image classification"
→ Creates project structure
→ Sets up data loaders
→ Implements basic training loop
→ Adds evaluation metrics
```

### 2. **Scaling Experiments**
```
"I need to scale this to 8 GPUs"
→ Modifies code for distributed training
→ Sets up DDP or FSDP
→ Handles data sharding
→ Adjusts hyperparameters for larger batch sizes
```

### 3. **Paper Implementation**
```
"Can you help me implement this paper: [arxiv link]"
→ Reads and understands the paper
→ Identifies key components
→ Implements step by step
→ Validates against paper results
```

## Tips for Best Results

1. **Be Specific**: "Train ResNet50 on CIFAR-10" vs. "train a model"
2. **Share Context**: Current setup, hardware, constraints
3. **Ask for Explanations**: Dr. Nova excels at teaching
4. **Iterate**: Start simple, add complexity gradually

## Character Personality

Dr. Nova is:
- **Patient**: Takes time to understand your problem
- **Methodical**: Approaches issues systematically
- **Practical**: Focuses on what works, not just theory
- **Encouraging**: Celebrates successes, learns from failures
- **Efficient**: Always considers compute and time costs

---

Happy researching! 🚀 Remember, the best model is one that actually trains and gives useful results, not necessarily the most complex one.