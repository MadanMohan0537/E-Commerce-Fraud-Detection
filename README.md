# FraudShield

FraudShield is a Cloudflare-native e-commerce fraud risk prototype. A static browser interface submits transaction attributes to a Cloudflare Worker, which returns a transparent rule-based risk score and the triggered risk factors.

> This is a portfolio/demo decision aid. It is not a trained production fraud model and must not be used to automatically approve, decline, or block real transactions.

## Architecture

- `public/index.html` — static frontend served by Workers Static Assets
- `worker/index.js` — validated `POST /predict` API and `GET /health`
- `wrangler.jsonc` — Cloudflare Workers and asset configuration
- `training/train_model.py` — optional offline XGBoost experiment; not used by the deployed Worker

## Run locally

```bash
npm run check
npm run dev
```

Open the local URL printed by Wrangler.

## Deploy

```bash
npx wrangler login
npm run deploy
```

No environment variables, Python runtime, model download, or paid inference API is required.

## API

```bash
curl -X POST http://localhost:8787/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction_amount":6000,"account_age_days":5,"num_transactions_today":8,"distance_from_home_km":900,"hour_of_day":2,"is_international":1,"failed_attempts":3}'
```

The response includes `probability`, the thresholded `fraud` flag, a risk label, and human-readable risk factors. The score is a deterministic heuristic—not a calibrated probability from a trained model.

## Production roadmap

Before using real transaction data:

- train and evaluate on representative, consented data;
- report precision, recall, false-positive rate, PR-AUC, and calibration—not accuracy alone;
- deploy a supported model format or external inference service;
- add authentication, durable rate limiting, audit logs, monitoring, and human review;
- perform privacy, security, fairness, and regulatory review.

## Offline training experiment

The Python training script is preserved for experimentation only:

```bash
pip install -r requirements-training.txt
python training/train_model.py
```

Its pickle output cannot run inside Cloudflare Workers. A separately validated export and inference architecture would be required.
