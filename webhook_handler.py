"""
Stripe Webhook Handler for JunctionSim
Processes payment events and updates user credits automatically
"""

import stripe
import json
import os
from supabase import create_client
from datetime import datetime

class StripeWebhookHandler:
    """Handles Stripe webhooks for automatic credit management"""
    
    def __init__(self):
        # Initialize Stripe with webhook secret
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SIGNING_SECRET")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_email = os.getenv("EMAIL")
        self.service_password = os.getenv("PASSWORD")
        
        stripe.api_key = self.stripe_api_key
        
    def verify_webhook_signature(self, payload, signature):
        """Verify that the webhook is genuinely from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except ValueError as e:
            # Invalid payload
            print(f"Invalid payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            print(f"Invalid signature: {e}")
            return None
    
    def get_supabase_client(self):
        """Get authenticated Supabase client"""
        try:
            supabase = create_client(self.supabase_url, self.supabase_key)
            
            # Sign in with service account
            auth_response = supabase.auth.sign_in_with_password({
                "email": self.service_email,
                "password": self.service_password
            })
            
            return supabase
            
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None
    
    async def handle_checkout_session_completed(self, session):
        """Process successful checkout sessions"""
        try:
            user_email = session.get('customer_details', {}).get('email')
            amount_total = session.get('amount_total', 0)
            session_id = session.get('id')
            
            if not user_email:
                print("No customer email found in session")
                return {"error": "No customer email"}
            
            # Convert amount from cents to credits
            # $1.00 = 10 credits (0.10 per simulation)
            credits_to_add = int(amount_total / 10)
            
            # Get database client
            supabase = self.get_supabase_client()
            if not supabase:
                return {"error": "Database connection failed"}
            
            # Get current user credits
            user_data = supabase.table('users').select('credits').eq('email', user_email).execute()
            
            if user_data.data:
                current_credits = user_data.data[0].get('credits', 0)
                new_credits = current_credits + credits_to_add
                
                # Update user credits
                update_result = supabase.table('users').update({
                    'credits': new_credits,
                    'last_purchase': datetime.utcnow().isoformat(),
                    'total_spent': amount_total / 100  # Convert to dollars
                }).eq('email', user_email).execute()
                
                if update_result.data:
                    print(f"Updated credits for {user_email}: {current_credits} → {new_credits}")
                    
                    # Log the transaction
                    supabase.table('transactions').insert({
                        'user_email': user_email,
                        'session_id': session_id,
                        'amount': amount_total / 100,
                        'credits_added': credits_to_add,
                        'timestamp': datetime.utcnow().isoformat(),
                        'type': 'credit_purchase'
                    }).execute()
                    
                    return {"success": True, "new_credits": new_credits}
                else:
                    return {"error": "Failed to update credits"}
            else:
                # Create new user record
                supabase.table('users').insert({
                    'email': user_email,
                    'credits': credits_to_add,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_purchase': datetime.utcnow().isoformat(),
                    'total_spent': amount_total / 100,
                    'subscription_tier': 'free'
                }).execute()
                
                print(f"Created new user {user_email} with {credits_to_add} credits")
                return {"success": True, "new_credits": credits_to_add}
                
        except Exception as e:
            print(f"Error processing checkout session: {e}")
            return {"error": str(e)}
    
    async def handle_invoice_payment_succeeded(self, invoice):
        """Process successful subscription payments"""
        try:
            subscription_id = invoice.get('subscription')
            customer_email = invoice.get('customer_email')
            amount_paid = invoice.get('amount_paid', 0)
            
            # Get subscription details
            subscription = stripe.Subscription.retrieve(subscription_id)
            product_id = subscription['items']['data'][0]['price']['product']
            product = stripe.Product.retrieve(product_id)
            
            # Get database client
            supabase = self.get_supabase_client()
            if not supabase:
                return {"error": "Database connection failed"}
            
            # Update user subscription status
            if 'Premium' in product['name']:
                subscription_tier = 'premium'
                # Add unlimited credits or set subscription flag
                update_data = {
                    'subscription_tier': subscription_tier,
                    'subscription_id': subscription_id,
                    'subscription_active': True,
                    'last_payment': datetime.utcnow().isoformat()
                }
            else:
                # Enterprise or custom plan
                subscription_tier = 'enterprise'
                update_data = {
                    'subscription_tier': subscription_tier,
                    'subscription_id': subscription_id,
                    'subscription_active': True,
                    'last_payment': datetime.utcnow().isoformat()
                }
            
            result = supabase.table('users').update(update_data).eq('email', customer_email).execute()
            
            if result.data:
                print(f"Updated subscription for {customer_email}: {subscription_tier}")
                
                # Log the subscription payment
                supabase.table('transactions').insert({
                    'user_email': customer_email,
                    'subscription_id': subscription_id,
                    'amount': amount_paid / 100,
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': 'subscription_payment'
                }).execute()
                
                return {"success": True, "subscription_tier": subscription_tier}
            else:
                return {"error": "Failed to update subscription"}
                
        except Exception as e:
            print(f"Error processing subscription payment: {e}")
            return {"error": str(e)}
    
    async def handle_subscription_deleted(self, subscription):
        """Process subscription cancellations"""
        try:
            customer_email = subscription.get('customer_email')
            
            # Get database client
            supabase = self.get_supabase_client()
            if not supabase:
                return {"error": "Database connection failed"}
            
            # Deactivate subscription
            result = supabase.table('users').update({
                'subscription_active': False,
                'subscription_cancelled': datetime.utcnow().isoformat()
            }).eq('email', customer_email).execute()
            
            if result.data:
                print(f"Cancelled subscription for {customer_email}")
                return {"success": True}
            else:
                return {"error": "Failed to cancel subscription"}
                
        except Exception as e:
            print(f"Error processing subscription cancellation: {e}")
            return {"error": str(e)}
    
    async def process_webhook(self, payload, signature):
        """Main webhook processing function"""
        # Verify webhook signature
        event = self.verify_webhook_signature(payload, signature)
        if not event:
            return {"error": "Invalid webhook signature"}
        
        # Handle different event types
        event_type = event['type']
        event_data = event['data']['object']
        
        print(f"Processing webhook event: {event_type}")
        
        if event_type == 'checkout.session.completed':
            return await self.handle_checkout_session_completed(event_data)
        
        elif event_type == 'invoice.payment_succeeded':
            return await self.handle_invoice_payment_succeeded(event_data)
        
        elif event_type == 'customer.subscription.deleted':
            return await self.handle_subscription_deleted(event_data)
        
        else:
            print(f"Unhandled event type: {event_type}")
            return {"success": True, "message": f"Event {event_type} received"}

# Supabase Edge Function (for deployment)
# Save this as supabase/functions/stripe-webhook/index.ts

EDGE_FUNCTION_CODE = '''
import Stripe from 'https://esm.sh/stripe@14.25.0?target=denonext'
import { createClient } from 'jsr:@supabase/supabase-js@2'

const stripe = new Stripe(Deno.env.get('STRIPE_API_KEY') as string, {
  apiVersion: '2024-11-20'
})

const cryptoProvider = Stripe.createSubtleCryptoProvider()

Deno.serve(async (request) => {
  // Verify webhook signature
  const signature = request.headers.get('Stripe-Signature')
  const body = await request.text()
  let receivedEvent

  try {
    receivedEvent = await stripe.webhooks.constructEventAsync(
      body,
      signature!,
      Deno.env.get('STRIPE_WEBHOOK_SIGNING_SECRET')!,
      undefined,
      cryptoProvider
    )
  } catch (err) {
    if (err instanceof Error) {
      return new Response(err.message, { status: 400 })
    }
    return new Response('Unknown error occurred', { status: 400 })
  }

  // Initialize Supabase client
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!
  )

  // Authenticate with service account
  try {
    const { error: loginError } = await supabase.auth.signInWithPassword({
      email: Deno.env.get('EMAIL')!,
      password: Deno.env.get('PASSWORD')!,
    })

    if (loginError) {
      throw loginError
    }
  } catch (error) {
    console.error('Authentication error:', error)
    return new Response('Authentication failed', { status: 500 })
  }

  // Handle events
  if (receivedEvent.type === 'checkout.session.completed') {
    const session = receivedEvent.data.object
    const userEmail = session.customer_details.email
    const amount = session.amount_total
    const sessionId = session.id

    try {
      // Get current user credits
      const { data: userData, error: fetchError } = await supabase
        .from('users')
        .select('credits')
        .eq('email', userEmail)
        .single()

      if (fetchError) {
        throw fetchError
      }

      // Calculate new credits (1 USD = 10 credits)
      const currentCredits = userData?.credits || 0
      const creditsToAdd = Math.floor(amount / 10)
      const newCredits = currentCredits + creditsToAdd

      // Update user credits
      const { error: updateError } = await supabase
        .from('users')
        .update({ 
          credits: newCredits,
          last_purchase: new Date().toISOString(),
          total_spent: amount / 100
        })
        .eq('email', userEmail)

      if (updateError) {
        throw updateError
      }

      console.log(`Updated credits for ${userEmail}: ${currentCredits} → ${newCredits}`)

      // Log transaction
      await supabase
        .from('transactions')
        .insert({
          user_email: userEmail,
          session_id: sessionId,
          amount: amount / 100,
          credits_added: creditsToAdd,
          timestamp: new Date().toISOString(),
          type: 'credit_purchase'
        })

    } catch (error) {
      console.error(`Error updating credits for ${userEmail}:`, error)
      return new Response('Failed to update user credits', { status: 500 })
    }
  }

  return new Response(JSON.stringify({ ok: true }), { status: 200 })
})
'''

def create_database_schema():
    """Generate SQL schema for user management"""
    
    schema = """
-- JunctionSim Database Schema
-- Run this in your Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  credits INTEGER DEFAULT 5,
  subscription_tier TEXT DEFAULT 'free',
  subscription_id TEXT,
  subscription_active BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_purchase TIMESTAMP WITH TIME ZONE,
  last_payment TIMESTAMP WITH TIME ZONE,
  total_spent DECIMAL DEFAULT 0,
  subscription_cancelled TIMESTAMP WITH TIME ZONE
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_email TEXT NOT NULL,
  session_id TEXT,
  subscription_id TEXT,
  amount DECIMAL NOT NULL,
  credits_added INTEGER,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  type TEXT NOT NULL,
  status TEXT DEFAULT 'completed'
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date DATE NOT NULL,
  daily_revenue DECIMAL DEFAULT 0,
  new_users INTEGER DEFAULT 0,
  active_subscriptions INTEGER DEFAULT 0,
  credits_purchased INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_transactions_user_email ON transactions(user_email);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date);

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own data" ON users
  FOR ALL USING (auth.email() = email);

CREATE POLICY "Users can view own transactions" ON transactions
  FOR ALL USING (auth.email() = user_email);

-- Service account can access all data
CREATE POLICY "Service account full access" ON users
  FOR ALL USING (auth.email() = 'service@junctionsim.com');

CREATE POLICY "Service account full transactions access" ON transactions
  FOR ALL USING (auth.email() = 'service@junctionsim.com');

-- Analytics is read-only for authenticated users
CREATE POLICY "Authenticated users can view analytics" ON analytics
  FOR SELECT USING (auth.role() = 'authenticated');
"""

    return schema

if __name__ == "__main__":
    # Example usage and testing
    print("Stripe Webhook Handler for JunctionSim")
    print("=" * 50)
    
    # Print database schema
    print("\nDatabase Schema:")
    print(create_database_schema())
    
    # Print edge function code
    print("\nEdge Function Code (save to supabase/functions/stripe-webhook/index.ts):")
    print(EDGE_FUNCTION_CODE)
    
    print("\nSetup Instructions:")
    print("1. Install dependencies: pip install stripe supabase")
    print("2. Set environment variables in Supabase Edge Functions")
    print("3. Deploy edge function: supabase functions deploy stripe-webhook")
    print("4. Configure webhook in Stripe Dashboard")
    print("5. Test with Stripe CLI: stripe listen --forward-to localhost:8000")