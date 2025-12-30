# JunctionSim Monetization Package

Complete payment processing system for JunctionSim with Stripe integration and direct bank deposits.

## 📦 What's Included

- **`stripe_integration_guide.py`** - Streamlit app with payment interface, pricing tiers, and revenue dashboard
- **`webhook_handler.py`** - Python webhook handler reference (for custom deployments)
- **`supabase_edge_function_stripe_webhook.ts`** - Production webhook handler for Supabase Edge Functions
- **`database_schema.sql`** - SQL schema for users, transactions, and analytics tables
- **`.streamlit/secrets.toml`** - Configuration template for Stripe and Supabase credentials
- **`requirements.txt`** - Python dependencies
- **`DEPLOYMENT_GUIDE.md`** - Complete setup and deployment instructions
- **`monetization_strategy.md`** - Business strategy and revenue projections
- **`README_MONETIZATION.md`** - Feature overview and revenue potential

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get API Keys
- **Stripe**: https://dashboard.stripe.com/apikeys
- **Supabase**: https://app.supabase.com/project/_/settings/api

### 3. Configure Secrets
Edit `.streamlit/secrets.toml`:
```toml
[stripe]
API_KEY = "sk_live_..."
PUBLISHABLE_KEY = "pk_live_..."
SUCCESS_URL = "https://your-app.streamlit.app"

[database]
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_key_here"
```

### 4. Setup Database
Run `database_schema.sql` in your Supabase SQL Editor

### 5. Run App
```bash
streamlit run stripe_integration_guide.py
```

## 💰 Revenue Model

| Tier | Price | Features |
|------|-------|----------|
| **Free** | Free | 5 simulations/day |
| **Basic** | $10 | 100 credits |
| **Premium** | $25/month | Unlimited simulations |
| **Enterprise** | Custom | Bulk licensing |

## 📊 Financial Projections

- **Month 1**: $2,000-$8,000 revenue
- **Month 6**: $25,000-$50,000 revenue
- **Year 1**: $150,000-$500,000 potential

See `monetization_strategy.md` for detailed projections.

## 🏦 Bank Deposits

- **Processor**: Stripe (recommended)
- **Timeline**: 2-7 business days to your bank account
- **Fees**: 2.9% + $0.30 per transaction
- **Instant Payouts**: Available (0.5% fee, 30 min arrival)

## 🔧 Deployment

### Development
```bash
streamlit run stripe_integration_guide.py
```

### Production
1. Push to GitHub
2. Deploy to Streamlit Cloud with secrets
3. Deploy webhook to Supabase Edge Functions
4. Configure Stripe webhook endpoint

See `DEPLOYMENT_GUIDE.md` for detailed steps.

## 🧪 Testing

Use Stripe test cards:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`

Expiry: any future date | CVC: any 3 digits

## 📖 Documentation

- **Setup**: See `DEPLOYMENT_GUIDE.md`
- **Business Strategy**: See `monetization_strategy.md`
- **Features**: See `README_MONETIZATION.md`

## 🔒 Security

- PCI DSS compliant (Stripe handles payment data)
- Webhook signature verification
- Row-level security in Supabase
- Encrypted data transmission

## 📞 Support

- **Stripe Docs**: https://docs.stripe.com
- **Supabase Docs**: https://supabase.com/docs
- **Streamlit Docs**: https://docs.streamlit.io

## 📝 License

This monetization package is provided as-is for educational and commercial use.

---

**First Payment**: Expected within 7-10 days of first customer purchase
**Setup Time**: 2-3 hours for complete deployment
**Ongoing Revenue**: Direct deposits to your bank account automatically
