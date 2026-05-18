# Running the §7 ablation locally on your Mac

This is the recommended path for the lean and full stages. More reliable than Colab for unattended runs because your Mac doesn't disconnect.

## One-time setup

```bash
# Clone the repo if you haven't
git clone https://github.com/vasundras/agent-runtime-patterns.git ~/agent-runtime-patterns
cd ~/agent-runtime-patterns

# Python deps
pip3 install --user 'anthropic>=0.39'

# API key (DO NOT commit this to git)
echo "export ANTHROPIC_API_KEY='sk-ant-...'" >> ~/.zshrc
source ~/.zshrc

# Results directory (somewhere outside the repo so git doesn't see it)
mkdir -p ~/agent-runtime-results
```

## Run unattended overnight

The pattern: `caffeinate -i` prevents your Mac from sleeping; `nohup` keeps the process alive across terminal logout; `&` backgrounds it; `> file 2>&1` captures both stdout and stderr to a log.

```bash
cd ~/agent-runtime-patterns

# Smoke first — verify the harness round-trips for ~$5
caffeinate -i nohup python3 evals/run_full_ablation.py \
    --results-dir ~/agent-runtime-results \
    --stage smoke \
    --live \
    > ~/agent-runtime-results/smoke.log 2>&1 &

# Check progress
tail -f ~/agent-runtime-results/smoke.log
# (Ctrl-C to stop tailing — the run continues in the background)
```

Once smoke is clean, kick off lean overnight:

```bash
caffeinate -i nohup python3 evals/run_full_ablation.py \
    --results-dir ~/agent-runtime-results \
    --stage lean \
    --live \
    > ~/agent-runtime-results/lean.log 2>&1 &

# Note the PID so you can check on it / kill it later
echo "Started lean run, PID=$!"
```

In the morning, check the log and decide:

```bash
# Quick status
tail -30 ~/agent-runtime-results/lean.log

# Compute Δpass^k from what's done so far (safe to run during the run)
python3 evals/analyze.py --results-dir ~/agent-runtime-results

# If the lean numbers support the hypothesis, kick off full:
caffeinate -i nohup python3 evals/run_full_ablation.py \
    --results-dir ~/agent-runtime-results \
    --stage full \
    --live \
    --auto-proceed \
    > ~/agent-runtime-results/full.log 2>&1 &
```

## Resume after interruption

If the process dies for any reason — Mac restart, Ctrl-C, network blip, API outage — just re-run the same command. Each scenario's JSONL row is fsync'd immediately on completion. Re-running scans existing JSONL files and skips any task_id already in them. No double-spending.

```bash
# Same command as before, exits quickly with "resuming — X scenarios already done"
caffeinate -i nohup python3 evals/run_full_ablation.py \
    --results-dir ~/agent-runtime-results \
    --stage lean \
    --live \
    > ~/agent-runtime-results/lean.resume.log 2>&1 &
```

## Monitoring while it runs

```bash
# How many scenarios in each result file?
wc -l ~/agent-runtime-results/*.jsonl

# How much have we spent so far?
python3 -c "
import json, sys
total = 0
with open('$HOME/agent-runtime-results/cost_ledger.jsonl') as f:
    for line in f:
        total += json.loads(line)['cost_usd']
print(f'Spent so far: \${total:.2f}')
"

# Latest heartbeat from the log
grep heartbeat ~/agent-runtime-results/*.log | tail -5
```

## Stopping cleanly

```bash
# Find the PID
ps aux | grep run_full_ablation | grep -v grep

# Soft stop (lets the current scenario finish and write before exiting)
kill <PID>

# Hard stop (loses the current scenario only; all prior are durable on disk)
kill -9 <PID>
```

## Cost guardrails

Set a billing alert in the Anthropic console at \$50, \$200, \$400 before starting. The cost ledger gives you a live total too:

```bash
watch -n 60 'python3 -c "
import json
total = 0
with open(\"$HOME/agent-runtime-results/cost_ledger.jsonl\") as f:
    for line in f:
        total += json.loads(line)[\"cost_usd\"]
print(f\"\${total:.2f}\")
"'
```

## When it's done

The JSONL files in `~/agent-runtime-results/` are the source of truth. Send them to me (paste the contents or attach) and I'll write the §7 results paragraph against the real numbers.
