# JunctionSim Monetization Setup & Deployment Guide

## Quick Start (15 minutes)

### 1. Create Stripe Account & Get API Keys
1. Visit https://stripe.com and create an account
2. Go to **Developers** → **API Keys**
3. Copy your **Secret Key** (starts with `sk_test_` or `sk_live_`)
4. Copy your **Publishable Key** (starts with `pk_test_` or `pk_live_`)

### 2. Create Supabase Project & Get Connection Keys
1. Visit https://app.supabase.com
2. Create new project (or use existing)
3. Go to **Settings** → **API**
4. Copy `Project URL` and `anon public` key
5. Under **Database** → **SQL Editor**, run the SQL from `database_schema.sql`

### 3. Configure Secrets
Edit `.streamlit/secrets.toml` and fill in:
```toml
[stripe]
API_KEY = "sk_test_your_key_here"
PUBLISHABLE_KEY = "pk_test_your_key_here"
SUCCESS_URL = "https://your-app.streamlit.app"
WEBHOOK_SECRET = "whsec_test_your_webhook_secret"

[database]
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_key_here"
SUPABASE_SERVICE_ROLE_KEY = "your_service_role_key_here"

[app]
SUPPORT_EMAIL = "support@junctionsim.com"
SALES_EMAIL = "sales@junctionsim.com"
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run Locally
```bash
streamlit run stripe_integration_guide.py
```

## Production Deployment

### Deploy to Streamlit Cloud

1. Push code to GitHub repository
2. Go to https://share.streamlit.io
3. Click "New app" and connect your repo
4. Set secrets in the Streamlit Cloud dashboard:
   - Copy contents of `.streamlit/secrets.toml` into "Secrets"
5. Deploy!

### Deploy Stripe Webhook Handler

#### Option A: Supabase Edge Functions (Recommended)

```bash
# 1. Install Supabase CLI
npm install -g supabase

# 2. Navigate to project
cd /path/to/project

# 3. Create function directory
mkdir -p supabase/functions/stripe-webhook

# 4. Copy the webhook handler
cp supabase_edge_function_stripe_webhook.ts supabase/functions/stripe-webhook/index.ts

# 5. Create environment variables file
cat > supabase/.env.local << EOF
STRIPE_API_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SIGNING_SECRET=whsec_your_secret_here
EOF

# 6. Deploy function
supabase functions deploy stripe-webhook --no-verify-jwt
```

#### Option B: Cloud Run (Google Cloud)

1. Build Docker image with webhook handler
2. Deploy to Cloud Run
3. Set environment variables
4. Update Stripe webhook endpoint URL

### Setup Stripe Webhook

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://your-supabase-url/functions/v1/stripe-webhook`
4. Select events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`
5. Copy the **Signing Secret** (starts with `whsec_`)
6. Add to `.streamlit/secrets.toml` as `WEBHOOK_SECRET`

## Database Setup

### Option 1: Supabase (Recommended)

1. Create Supabase project at https://app.supabase.com
2. Go to **SQL Editor**
3. Run SQL from `database_schema.sql`
4. Tables created:
   - `users` - User credits and subscription status
   - `transactions` - Payment history
   - `analytics` - Revenue tracking

### Option 2: Self-hosted PostgreSQL

Update connection string in `.streamlit/secrets.toml`:
```toml
[database]
DATABASE_URL = "postgresql://user:password@localhost:5432/junctionsim"
```

## Testing Payments

### Local Testing with Stripe Test Keys

Use these test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Auth Required**: `4000 0025 0000 3155`
- Expiry: any future date
- CVC: any 3 digits

### Test Webhook Locally

```bash
# Install Stripe CLI
# macOS: brew install stripe/stripe-cli/stripe

# Start webhook forwarding
stripe listen --forward-to localhost:8501/webhook

# Get signing secret and add to secrets.toml
```

## Monitoring & Analytics

### Check Revenue in Real-time

1. Go to Supabase dashboard
2. Open **transactions** table
3. Filter by `type = 'credit_purchase'` or `type = 'subscription_payment'`
4. Sum the `amount` column

### View User Analytics

Query top spenders:
```sql
SELECT 
  email,
  SUM(CAST(amount AS FLOAT)) as total_spent,
  COUNT(*) as transaction_count,
  MAX(timestamp) as last_purchase
FROM transactions
GROUP BY email
ORDER BY total_spent DESC
LIMIT 10;
```

## Troubleshooting

### "Stripe configuration missing" error
- Check `.streamlit/secrets.toml` exists
- Verify API_KEY format (should start with `sk_`)
- Restart Streamlit: `streamlit run stripe_integration_guide.py --logger.level=debug`

### Webhook not triggering
- Check webhook URL in Stripe Dashboard is accessible
- Verify `STRIPE_WEBHOOK_SIGNING_SECRET` is correct
- Check Supabase function logs

### Credits not updating after purchase
- Verify webhook handler is deployed
- Check transaction logs in Supabase for errors
- Ensure user email matches Stripe checkout email

### Database connection errors
- Verify Supabase URL and key are correct
- Check RLS policies are enabled
- Ensure tables exist (run schema SQL)

## Environment Variables Reference

| Variable | Required | Example | Source |
|----------|----------|---------|--------|
| `STRIPE_API_KEY` | Yes | `sk_live_...` | Stripe Dashboard → Developers |
| `STRIPE_WEBHOOK_SECRET` | Yes | `whsec_...` | Stripe Dashboard → Webhooks |
| `SUPABASE_URL` | Yes | `https://abc.supabase.co` | Supabase Settings → API |
| `SUPABASE_KEY` | Yes | `eyJ0...` | Supabase Settings → API |
| `SUCCESS_URL` | Yes | `https://app.streamlit.app` | Your deployed app URL |
| `APP_NAME` | No | `JunctionSim` | Custom |
| `ENABLE_ANALYTICS` | No | `true` | Custom |

## Security Checklist

- [ ] Using `sk_live_` keys in production (not `sk_test_`)
- [ ] Webhook secret properly configured
- [ ] Secrets stored in `.streamlit/secrets.toml` (not in code)
- [ ] `.env` files added to `.gitignore`
- [ ] HTTPS enforced for all endpoints
- [ ] Row-level security (RLS) enabled in Supabase
- [ ] Regular security audits of payment code

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Configure secrets in `.streamlit/secrets.toml`
3. ✅ Run database schema SQL in Supabase
4. ✅ Deploy to Streamlit Cloud
5. ✅ Deploy webhook handler to Supabase
6. ✅ Configure Stripe webhook endpoint
7. ✅ Test with Stripe test cards
8. ✅ Switch to live keys when ready

## Support

- **Stripe Issues**: https://support.stripe.com
- **Supabase Issues**: https://supabase.com/docs
- **Streamlit Issues**: https://discuss.streamlit.io
- **Custom Help**: See SUPPORT_EMAIL in config

---

**First Payment to Bank Account**: 2-7 business days after first transaction (depending on country/payout schedule)
