// Supabase Edge Function for Stripe Webhook
// Deploy with: supabase functions deploy stripe-webhook
// Add environment variables to .env.local:
// - STRIPE_API_KEY
// - STRIPE_WEBHOOK_SIGNING_SECRET

import Stripe from "https://esm.sh/stripe@14.25.0?target=deno";

const stripe = new Stripe(Deno.env.get("STRIPE_API_KEY") || "", {
  apiVersion: "2024-11-20",
});

const cryptoProvider = Stripe.createSubtleCryptoProvider();

Deno.serve(async (request: Request) => {
  const signature = request.headers.get("Stripe-Signature");
  const body = await request.text();

  let receivedEvent: Stripe.Event;

  try {
    receivedEvent = await stripe.webhooks.constructEventAsync(
      body,
      signature!,
      Deno.env.get("STRIPE_WEBHOOK_SIGNING_SECRET")!,
      undefined,
      cryptoProvider
    );
  } catch (err) {
    if (err instanceof Error) {
      console.error("Webhook signature verification failed:", err.message);
      return new Response(err.message, { status: 400 });
    }
    return new Response("Unknown error occurred", { status: 400 });
  }

  console.log(`Processing webhook event: ${receivedEvent.type}`);

  // Handle events
  if (receivedEvent.type === "checkout.session.completed") {
    const session = receivedEvent.data.object as Stripe.Checkout.Session;
    const userEmail = session.customer_details?.email;
    const amount = session.amount_total || 0;
    const sessionId = session.id;

    if (!userEmail) {
      return new Response(JSON.stringify({ error: "No customer email" }), {
        status: 400,
      });
    }

    try {
      const { data: userData, error: fetchError } = await supabaseClient
        .from("users")
        .select("credits")
        .eq("email", userEmail)
        .single();

      if (fetchError && fetchError.code !== "PGRST116") {
        throw fetchError;
      }

      const currentCredits = userData?.credits || 0;
      const creditsToAdd = Math.floor(amount / 10); // $1 = 10 credits
      const newCredits = currentCredits + creditsToAdd;

      // Update user credits
      const { error: updateError } = await supabaseClient
        .from("users")
        .upsert(
          {
            email: userEmail,
            credits: newCredits,
            last_purchase: new Date().toISOString(),
            total_spent: (userData?.total_spent || 0) + amount / 100,
            subscription_tier: "free",
          },
          { onConflict: "email" }
        );

      if (updateError) {
        throw updateError;
      }

      // Log transaction
      await supabaseClient.from("transactions").insert({
        user_email: userEmail,
        session_id: sessionId,
        amount: amount / 100,
        credits_added: creditsToAdd,
        timestamp: new Date().toISOString(),
        type: "credit_purchase",
        status: "completed",
      });

      console.log(
        `Updated credits for ${userEmail}: ${currentCredits} → ${newCredits}`
      );

      return new Response(JSON.stringify({ success: true }), { status: 200 });
    } catch (error) {
      console.error(`Error updating credits for ${userEmail}:`, error);
      return new Response("Failed to update user credits", { status: 500 });
    }
  }

  if (receivedEvent.type === "invoice.payment_succeeded") {
    const invoice = receivedEvent.data.object as Stripe.Invoice;
    const customerEmail = invoice.customer_email;
    const amountPaid = invoice.amount_paid || 0;
    const subscriptionId = invoice.subscription;

    if (!customerEmail) {
      return new Response(JSON.stringify({ error: "No customer email" }), {
        status: 400,
      });
    }

    try {
      // Get subscription details
      const subscription = await stripe.subscriptions.retrieve(
        subscriptionId as string
      );
      const priceId =
        subscription.items.data[0]?.price.id ||
        subscription.items.data[0]?.price.product;
      const productId = subscription.items.data[0]?.price.product;
      const product = await stripe.products.retrieve(productId as string);

      const tier = product.name.includes("Premium") ? "premium" : "enterprise";

      // Update subscription status
      const { error: updateError } = await supabaseClient
        .from("users")
        .update({
          subscription_tier: tier,
          subscription_id: subscriptionId,
          subscription_active: true,
          last_payment: new Date().toISOString(),
        })
        .eq("email", customerEmail);

      if (updateError) {
        throw updateError;
      }

      // Log transaction
      await supabaseClient.from("transactions").insert({
        user_email: customerEmail,
        subscription_id: subscriptionId,
        amount: amountPaid / 100,
        timestamp: new Date().toISOString(),
        type: "subscription_payment",
        status: "completed",
      });

      console.log(`Updated subscription for ${customerEmail}: ${tier}`);

      return new Response(JSON.stringify({ success: true }), { status: 200 });
    } catch (error) {
      console.error(`Error processing subscription for ${customerEmail}:`, error);
      return new Response("Failed to update subscription", { status: 500 });
    }
  }

  if (receivedEvent.type === "customer.subscription.deleted") {
    const subscription = receivedEvent.data.object as Stripe.Subscription;
    const customerId = subscription.customer as string;

    try {
      // Get customer email
      const customer = await stripe.customers.retrieve(customerId);
      const customerEmail =
        customer.deleted === false ? customer.email : null;

      if (!customerEmail) {
        return new Response(
          JSON.stringify({ error: "Could not find customer email" }),
          { status: 400 }
        );
      }

      // Deactivate subscription
      const { error: updateError } = await supabaseClient
        .from("users")
        .update({
          subscription_active: false,
          subscription_cancelled: new Date().toISOString(),
        })
        .eq("email", customerEmail);

      if (updateError) {
        throw updateError;
      }

      console.log(`Cancelled subscription for ${customerEmail}`);

      return new Response(JSON.stringify({ success: true }), { status: 200 });
    } catch (error) {
      console.error(`Error cancelling subscription:`, error);
      return new Response("Failed to cancel subscription", { status: 500 });
    }
  }

  // Return 200 for unhandled event types to acknowledge receipt
  return new Response(JSON.stringify({ ok: true }), { status: 200 });
});
