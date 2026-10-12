# Invalidated measurements

The following routing measurements were produced by evaluator v1 and MUST NOT be used for model-quality conclusions:

- `smollm2-135m-instruct-fp32-v0.json`
- `smollm2-360m-instruct-fp32-v0.json`
- `qwen25-0p5b-instruct-fp32-v0.json`
- `qwen25-0p5b-instruct-fp32-ja-v1.json`

Reason: the batched evaluator rendered the chat template to text and then tokenized it with `add_special_tokens=True`, duplicating special-token framing. Single-request generation probes did not use this path and exposed the disagreement. Evaluator v2 sets `add_special_tokens=False` for already-rendered chat templates.

Keep these files as failure-biopsy evidence for the benchmark harness. Do not delete them.
