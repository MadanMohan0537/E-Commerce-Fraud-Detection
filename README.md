# FraudShield

An explainable e-commerce risk-scoring prototype with a Cloudflare Worker API and an interactive inspection UI.

**Current behavior:** the online endpoint uses deterministic rules. The separate Python training script is an offline experiment; its model is not served by the Worker. Scores are heuristic values, not calibrated fraud probabilities.

## What you can try

- Submit transaction attributes and inspect contributing risk factors.
- Compare high-amount, new-account, unusual-hour, distance and failed-attempt scenarios.
- Run the Worker locally or deploy it to your own Cloudflare account.
- Explore supervised classification separately with the Python training script.

[Demo application](https://e-commerce-fraud-detection.madanmohanlearning.workers.dev/)

## Quick start

Use a current Node.js version compatible with Wrangler 4 and npm.

```bash
git clone https://github.com/MadanMohan0537/E-Commerce-Fraud-Detection.git
cd E-Commerce-Fraud-Detection
npm install
npm run check
npm run dev
```

Open the URL printed by Wrangler, normally http://localhost:8787. The scripts invoke Wrangler 4.120.0 through `npx`; a global CLI installation is not required.

## API

### POST /predict

Send a JSON object with numeric transaction features. Omitted numeric fields use defaults defined in [worker/index.js](worker/index.js); invalid ranges return a validation error.

```bash
curl http://localhost:8787/predict \
  -H 'Content-Type: application/json' \
  -d '{"transaction_amount":6000,"account_age_days":5,"num_transactions_today":8,"distance_from_home_miles":2445,"hour_of_day":2,"is_international":1,"failed_attempts":3}'
```

The response includes:

| Field | Meaning |
| --- | --- |
| `fraud` | Whether the heuristic score exceeds 0.5 |
| `probability` | Rounded heuristic score, capped at 0.99; not a calibrated probability |
| `confidence` | Risk label derived from score thresholds |
| `risk_factors` | Objects containing `factor` and `severity` |
| `mode` | `rules` |
| `disclaimer` | Prototype decision-aid boundary |

The example above activates several rules. Inspect the actual response rather than relying on an illustrative risk score. The service does not maintain cross-request transaction history; velocity fields are supplied by the caller.

## Offline model experiment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-training.txt
python training/train_model.py
```

On Windows, activate with `.venv\Scripts\activate`. Review [the training script](training/train_model.py) before running it for its input and output assumptions. The online rule engine and offline model must be evaluated separately.

## Repository map

| Location | Purpose |
| --- | --- |
| [worker/index.js](worker/index.js) | Feature validation, risk rules and HTTP routes |
| [public](public/) | Browser application |
| [training/train_model.py](training/train_model.py) | Offline classification experiment |
| [requirements-training.txt](requirements-training.txt) | Python training dependencies |
| [wrangler.jsonc](wrangler.jsonc) | Worker deployment configuration |

## Validation and deployment

`npm run check` performs a JavaScript syntax check. It does not evaluate fraud detection accuracy. For your own deployment, review `wrangler.jsonc`, authenticate to Cloudflare and run `npm run deploy`.

## Limitations

This prototype has no published real-world fraud validation, calibrated probability estimate or latency benchmark. It should not independently approve or decline payments. Production use would need representative labeled data, threshold calibration, monitoring, authentication, abuse controls and a review process.

## Contributions and license

A useful contribution includes fixture-backed rule tests or a reproducible model evaluation. No license file is currently included; choose an explicit license before redistributing the implementation.
