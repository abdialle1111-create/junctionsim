"""
Stripe Integration Guide for JunctionSim
Complete payment processing implementation with direct bank deposits
"""

import streamlit as st
import stripe
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from supabase import create_client, Client
from typing import Optional, Dict

# Initialize Stripe with your secret key
# This should be stored in .streamlit/secrets.toml
# stripe.api_key = st.secrets["stripe"]["API_KEY"]

class JunctionSimPayments:
    """Complete payment processing system for JunctionSim"""
    
    def __init__(self):
        self.api_key = None  # Will be set from secrets
        self.success_url = None  # Will be set from secrets
        self.supabase: Optional[Client] = None
        
    def initialize_stripe(self) -> bool:
        """Initialize Stripe with API keys from secrets"""
        try:
            self.api_key = st.secrets["stripe"]["API_KEY"]
            self.success_url = st.secrets["stripe"]["SUCCESS_URL"]
            stripe.api_key = self.api_key
            return True
        except:
            st.error("Stripe configuration missing. Please add to secrets.toml")
            return False
    
    def create_checkout_session(self, amount: float, user_email: str, product_type: str = "credits") -> str:
        """
        Create a Stripe checkout session for purchases
        
        Args:
            amount: Dollar amount to charge
            user_email: User's email address
            product_type: Type of purchase ("credits", "subscription", "enterprise")
            
        Returns:
            str: Checkout session URL
        """
        try:
            if product_type == "credits":
                # One-time credit purchase
                checkout_session = stripe.checkout.Session.create(
                    customer_email=user_email,
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "JunctionSim Credits",
                                "description": f"{int(amount*10)} simulation credits"
                            },
                            "unit_amount": int(amount * 100),  # Convert to cents
                        },
                        "quantity": 1,
                    }],
                    mode="payment",
                    success_url=f"{self.success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{self.success_url}?cancelled=true",
                )
            
            elif product_type == "subscription":
                # Monthly premium subscription
                checkout_session = stripe.checkout.Session.create(
                    customer_email=user_email,
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "JunctionSim Premium",
                                "description": "Unlimited simulations and advanced features"
                            },
                            "unit_amount": 2500,  # $25.00
                            "recurring": {
                                "interval": "month"
                            }
                        },
                        "quantity": 1,
                    }],
                    mode="subscription",
                    success_url=f"{self.success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{self.success_url}?cancelled=true",
                )
            
            elif product_type == "enterprise":
                # Enterprise licensing (custom pricing)
                checkout_session = stripe.checkout.Session.create(
                    customer_email=user_email,
                    line_items=[{
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "JunctionSim Enterprise License",
                                "description": "Custom enterprise solution"
                            },
                            "unit_amount": int(amount * 100),
                        },
                        "quantity": 1,
                    }],
                    mode="payment",
                    success_url=f"{self.success_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{self.success_url}?cancelled=true",
                )
            
            return checkout_session.url
            
        except Exception as e:
            st.error(f"Error creating checkout session: {str(e)}")
            return None
    
    def get_user_credits(self, user_email: str) -> int:
        """
        Get user's current credit balance
        This would integrate with your database
        """
        # Mock implementation - replace with database call
        if user_email in st.session_state:
            return st.session_state.get('user_credits', 5)
        return 5
    
    def update_user_credits(self, user_email: str, credits: int):
        """
        Update user's credit balance
        This would integrate with your database
        """
        st.session_state['user_credits'] = credits
    
    def get_subscription_status(self, user_email: str) -> dict:
        """
        Check if user has active subscription
        """
        # Mock implementation - replace with database call
        return st.session_state.get('subscription', {'active': False, 'tier': 'free'})

def render_payment_interface():
    """Render the complete payment interface in Streamlit"""
    
    st.title("💳 JunctionSim Premium Features")
    
    # Initialize payment system
    payments = JunctionSimPayments()
    if not payments.initialize_stripe():
        st.warning("Payment system not configured. This is a demo interface.")
        demo_mode = True
    else:
        demo_mode = False
    
    # Get current user info (mock for demo)
    user_email = st.session_state.get('user_email', 'demo@junctionsim.com')
    
    # Display current account status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_credits = payments.get_user_credits(user_email)
        st.metric(
            "Available Credits", 
            current_credits,
            " simulations remaining today"
        )
    
    with col2:
        subscription = payments.get_subscription_status(user_email)
        if subscription['active']:
            st.metric("Subscription", subscription['tier'].upper(), "Active")
        else:
            st.metric("Subscription", "FREE", "Upgrade available")
    
    with col3:
        st.metric("Account Type", "Educational", "Verified ✓")
    
    st.divider()
    
    # Pricing Tiers
    st.header("Choose Your Plan")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔬 Basic Plan
        **Perfect for students**
        
        - 100 simulation credits
        - All p-n junction types
        - Export functionality
        - Email support
        """)
        st.markdown("#### **$10.00**")
        if st.button("Buy Basic Plan", key="basic"):
            if not demo_mode:
                checkout_url = payments.create_checkout_session(10, user_email, "credits")
                if checkout_url:
                    st.markdown(f"[Complete Purchase]({checkout_url})")
            else:
                st.info("Demo mode: This would redirect to Stripe checkout")
    
    with col2:
        st.markdown("""
        ### 🚀 Premium Plan
        **Best value for researchers**
        
        - Unlimited simulations
        - Advanced parameters
        - Priority support
        - Team collaboration
        - API access
        """)
        st.markdown("#### **$25.00 / month**")
        if st.button("Subscribe Premium", key="premium"):
            if not demo_mode:
                checkout_url = payments.create_checkout_session(25, user_email, "subscription")
                if checkout_url:
                    st.markdown(f"[Start Subscription]({checkout_url})")
            else:
                st.info("Demo mode: This would redirect to Stripe checkout")
    
    with col3:
        st.markdown("""
        ### 🏫 Enterprise Plan
        **For universities and companies**
        
        - Custom seat licenses
- Advanced analytics
        - Dedicated support
        - Custom integrations
        - Training sessions
        """)
        st.markdown("#### **Custom Pricing**")
        if st.button("Contact Sales", key="enterprise"):
            st.info("📧 sales@junctionsim.com\n\nWe'll create a custom quote for your institution!")
    
    st.divider()
    
    # Credit Purchase Options
    st.header("Quick Credit Purchase")
    
    credit_amount = st.select_slider(
        "Select credit package:",
        options=[5, 10, 25, 50, 100],
        value=25,
        format_func=lambda x: f"{x} credits (${x/10:.1f})"
    )
    
    if st.button(f"Purchase {credit_amount} Credits - ${credit_amount/10:.2f}"):
        if not demo_mode:
            checkout_url = payments.create_checkout_session(credit_amount/10, user_email, "credits")
            if checkout_url:
                st.markdown(f"[Complete Purchase]({checkout_url})")
        else:
            st.info(f"Demo mode: Would process ${credit_amount/10:.2f} payment")
            # Simulate adding credits
            new_credits = current_credits + credit_amount
            payments.update_user_credits(user_email, new_credits)
            st.success(f"Added {credit_amount} credits! New balance: {new_credits}")
            st.rerun()
    
    # Revenue Dashboard (for admin view)
    if st.checkbox("Show Revenue Dashboard (Admin)"):
        render_revenue_dashboard()

def render_revenue_dashboard():
    """Render revenue analytics dashboard"""
    
    st.header("💰 Revenue Analytics Dashboard")
    
    # Mock revenue data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    daily_revenue = pd.Series(
        [100 + i*2 + (i%7)*50 for i in range(len(dates))],
        index=dates
    )
    
    # Revenue chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_revenue.index,
        y=daily_revenue.values,
        mode='lines+markers',
        name='Daily Revenue',
        line=dict(color='#00E5CC', width=3)
    ))
    
    fig.update_layout(
        title="Daily Revenue Trend",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = daily_revenue.sum()
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    
    with col2:
        avg_daily = daily_revenue.mean()
        st.metric("Daily Average", f"${avg_daily:.0f}")
    
    with col3:
        total_users = 1250
        st.metric("Total Users", f"{total_users:,}")
    
    with col4:
        conversion_rate = 7.2
        st.metric("Conversion Rate", f"{conversion_rate}%")
    
    # Revenue by source
    st.subheader("Revenue by Source")
    
    revenue_sources = pd.DataFrame({
        'Source': ['Individual Plans', 'University Licensing', 'Premium Subscriptions', 'Enterprise'],
        'Revenue': [15000, 25000, 20000, 10000],
        'Percentage': [21.4, 35.7, 28.6, 14.3]
    })
    
    fig = go.Figure(data=[
        go.Pie(
            labels=revenue_sources['Source'],
            values=revenue_sources['Revenue'],
            hole=0.4,
            marker_colors=['#00E5CC', '#0F1B33', '#FF6B6B', '#4ECDC4']
        )
    ])
    
    fig.update_layout(
        title="Revenue Distribution",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_bank_setup_instructions():
    """Render instructions for setting up bank account"""
    
    st.header("🏦 Bank Account Setup for Direct Deposits")
    
    st.markdown("""
    ### Step 1: Connect Your Bank Account to Stripe
    
    1. Log into your [Stripe Dashboard](https://dashboard.stripe.com)
    2. Go to **Settings** → **Payouts**
    3. Click **Add bank account**
    4. Enter your bank details:
       - **US**: Account number + Routing number
       - **EU**: IBAN + SWIFT/BIC
       - **UK**: Sort code + Account number
    
    ### Step 2: Verify Your Bank Account
    
    Stripe will make small test deposits ($0.01-$0.05) to verify:
    - Check your bank account in 1-2 business days
    - Enter the exact amounts in Stripe Dashboard
    - Verification enables automatic payouts
    
    ### Step 3: Configure Payout Schedule
    
    **Recommended settings for JunctionSim:**
    - **Frequency**: Daily automatic payouts
    - **Minimum balance**: $10 (to avoid micro-payouts)
    - **Country**: Select your bank's location
    
    ### Step 4: Tax Information
    
    Complete tax verification to avoid payout delays:
    - **US**: Form W-9 for individuals, W-8BEN for non-US
    - **EU**: VAT number if applicable
    - **International**: Local tax identification
    
    ### Expected Payout Timeline
    
    | Country | Standard Speed | Same-Day Available |
    |---------|----------------|-------------------|
    | US | 2 business days | Yes |
    | UK | 2 business days | Yes |
    | EU | 3 business days | No |
    | Canada | 3 business days | No |
    | Australia | 3 business days | No |
    
    ### Instant Payouts (Optional)
    
    For immediate access to funds:
    - **Fee**: 0.5% per transfer
    - **Speed**: 30 minutes to bank account
    - **Availability**: US, UK, Canada, EU
    - **Limits**: $10,000 per transfer, 3 per day
    
    ### Virtual Bank Support
    
    Stripe supports these virtual banks:
    - **Revolut**, **Wise**, **N26** (Europe)
    - **Chime**, **Varo** (US)
    - **Monzo**, **Starling** (UK)
    
    Note: Virtual banks may have slightly higher failure rates.
    
    ### Security & Compliance
    
    ✅ **PCI DSS Compliance** - Handled by Stripe  
    ✅ **Bank-Level Encryption** - All data encrypted  
    ✅ **Fraud Detection** - Automatic monitoring  
    ✅ **Dispute Resolution** - Built-in chargeback handling  
    ✅ **Regulatory Compliance** - Global payment regulations  
    """)

if __name__ == "__main__":
    # Main app rendering
    tab1, tab2, tab3 = st.tabs(["💳 Payment Interface", "📊 Revenue Dashboard", "🏦 Bank Setup"])
    
    with tab1:
        render_payment_interface()
    
    with tab2:
        render_revenue_dashboard()
    
    with tab3:
        render_bank_setup_instructions()