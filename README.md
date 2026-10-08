# ModelOne: phishing email triage with System One models

Small Python script that sends an email to several **System One** models served by [Codiv](https://codiv.ai) and compares how each one answers.

System One models are *decision models*, not chat models. They don't write text: you give them a text and a set of typed questions, and they return a probability for each answer in a single pass (milliseconds). This models could be useful whenever you need a quick decision instead of generated text.They answer typed questions (yes/no, pick one, score) in milliseconds, with a probability attached to each answer.That makes them cheap to run at high volume and easy to automate, because you can act on thresholds without parsing any text. They’re not for writing, explaining, or multi-step reasoning, and the small ones should be validated on your own data first.

## How it works

1. You build a "form" of questions (`QUESTIONS`).
2. The model reads the text once and fills in every question.
3. You apply thresholds to decide what to automate and what a human must review.

### Question types

| Type     | What it asks                  | What you get back                                   |
|----------|-------------------------------|-----------------------------------------------------|
| `noul`   | Yes/no question               | Probability between 0 and 1                         |
| `choice` | Pick one option from a list   | Winning option, probability of each, `confidence`   |
| `score`  | Place the text on a scale     | Number between 0 and N-1, probabilities, `confidence` |

> **About `confidence`:** 1 means one option holds all the probability, 0 means all options are equally likely. It is **not** the chance of being right, only how decided the model is.

## Requirements

- Python 3.9+
- A free Codiv API key: <https://codiv.ai/signup>
- `requests`

```bash
pip install requests
```

## Setup

Store the key in an environment variable. Never hardcode it or commit it.

**Windows (PowerShell)**

```powershell
$env:CODIV_API_KEY="sk-codiv-..."
```

**Linux / macOS**

```bash
export CODIV_API_KEY=sk-codiv-...
```

## Usage

```bash
python ModelOne.py
```

The script runs the same email through every model in `MODELS` and prints the results side by side.

### Example output

```
=== laya-1.0 ===
Phishing? 80.0%
Type: phishing (confidence 0.13)
   phishing: 41.5%
   bec: 29.0%
   spam: 25.0%
   legitimate: 4.4%
Risk: 3.26 / 4 (confidence 0.28)
-> Manual review
```

Here the model leans towards phishing but is far from decided (confidence 0.13), so the rule sends the email to manual review. That is the intended behavior of thresholds.

## Models

| Model ID         | Input       | Notes                                      |
|------------------|-------------|--------------------------------------------|
| `laya-1.0`       | Text only   | 421M encoder, about 10 ms per request      |
| `verdict-1.4`    | Text only   | 151M encoder, about 7 ms per request       |
| `clm-v0.1`       | Text only   | Qwen3-8B based, about 100 ms per request   |
| `jevk5-0.2`      | Text only   | Qwen3.5-4B based, about 80 ms per request  |
| `openjev-latest` | Text + images | DiffusionGemma 26B-A4B, Apache-2.0       |

Figures come from the Codiv website and may change.

## Configuration

Everything you will want to tweak is at the top of `ModelOne.py`:

- `MODELS`: which models to compare.
- `EMAIL`: the text to analyze (called `state` in the API).
- `QUESTIONS`: the form the model fills in.
- Decision rule at the bottom:

## Tips

- Prefer `noul` (yes/no) questions for decisions. They tend to be clearer for the model than splitting probability across several similar options.
- Keep `choice` options clearly different from each other. Overlapping options spread the probability and lower the confidence.
- Ask all the questions you need in one request: the text is read once, so a batch of questions is cheaper than one request each.
- Small models may perform differently depending on the language of the email. Test both.

## Limits (free plan)

- 60 requests per minute per key
- 100M System One tokens per account


