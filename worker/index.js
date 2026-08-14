const DEFAULTS = {
  transaction_amount: 0,
  account_age_days: 365,
  num_transactions_today: 1,
  distance_from_home_km: 0,
  hour_of_day: 12,
  is_weekend: 0,
  is_international: 0,
  payment_method: 0,
  device_type: 0,
  failed_attempts: 0,
}

const LIMITS = {
  transaction_amount: [0, 10_000_000],
  account_age_days: [0, 36_500],
  num_transactions_today: [0, 10_000],
  distance_from_home_km: [0, 50_000],
  hour_of_day: [0, 23],
  is_weekend: [0, 1],
  is_international: [0, 1],
  payment_method: [0, 2],
  device_type: [0, 2],
  failed_attempts: [0, 1_000],
}

const JSON_HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'cache-control': 'no-store',
  'x-content-type-options': 'nosniff',
}

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...JSON_HEADERS, ...extraHeaders },
  })
}

function parseFeatures(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw new Error('Request body must be a JSON object.')
  }

  const result = {}
  for (const [name, fallback] of Object.entries(DEFAULTS)) {
    const raw = body[name] ?? fallback
    const value = Number(raw)
    const [min, max] = LIMITS[name]
    if (!Number.isFinite(value) || value < min || value > max) {
      throw new Error(`${name} must be a number between ${min} and ${max}.`)
    }
    result[name] = value
  }
  return result
}

function heuristicScore(f) {
  let score = 0
  if (f.transaction_amount > 5000) score += 0.35
  else if (f.transaction_amount > 1000) score += 0.15
  if (f.account_age_days < 30) score += 0.2
  if (f.num_transactions_today > 5) score += 0.15
  if (f.distance_from_home_km > 500) score += 0.2
  if (f.hour_of_day < 5 || f.hour_of_day > 22) score += 0.15
  if (f.is_international === 1) score += 0.1
  if (f.failed_attempts > 1) score += 0.2
  return Math.min(score, 0.99)
}

function confidenceLabel(probability) {
  if (probability > 0.85) return 'Very High Risk'
  if (probability > 0.65) return 'High Risk'
  if (probability > 0.45) return 'Medium Risk'
  if (probability > 0.25) return 'Low Risk'
  return 'Very Low Risk'
}

function riskFactors(f) {
  const factors = []
  if (f.transaction_amount > 5000) factors.push({ factor: 'High transaction amount', severity: 'high' })
  else if (f.transaction_amount > 1000) factors.push({ factor: 'Elevated transaction amount', severity: 'medium' })
  if (f.account_age_days < 30) factors.push({ factor: 'New account (< 30 days)', severity: 'high' })
  if (f.num_transactions_today > 5) factors.push({ factor: 'Multiple transactions today', severity: 'medium' })
  if (f.distance_from_home_km > 500) factors.push({ factor: 'Transaction far from home', severity: 'high' })
  if (f.hour_of_day < 5 || f.hour_of_day > 22) factors.push({ factor: 'Unusual transaction time', severity: 'medium' })
  if (f.is_international === 1) factors.push({ factor: 'International transaction', severity: 'low' })
  if (f.failed_attempts > 1) factors.push({ factor: 'Previous failed attempts', severity: 'high' })
  if (!factors.length) factors.push({ factor: 'No significant rule-based risk factors detected', severity: 'none' })
  return factors
}

async function predict(request) {
  if (!request.headers.get('content-type')?.includes('application/json')) {
    return json({ error: 'Content-Type must be application/json.' }, 415)
  }

  const contentLength = Number(request.headers.get('content-length') || 0)
  if (contentLength > 16_384) return json({ error: 'Request body is too large.' }, 413)

  try {
    const features = parseFeatures(await request.json())
    const probability = heuristicScore(features)
    return json({
      fraud: probability > 0.5,
      probability: Math.round(probability * 1000) / 1000,
      confidence: confidenceLabel(probability),
      risk_factors: riskFactors(features),
      mode: 'rules',
      disclaimer: 'Prototype decision aid only; not a production fraud decision system.',
    })
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Invalid request.' }, 400)
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)

    if (url.pathname === '/health' && request.method === 'GET') {
      return json({ status: 'ok', runtime: 'cloudflare-workers', mode: 'rules' })
    }

    if (url.pathname === '/predict') {
      if (request.method !== 'POST') {
        return json({ error: 'Method not allowed.' }, 405, { allow: 'POST' })
      }
      return predict(request)
    }

    return env.ASSETS.fetch(request)
  },
}
