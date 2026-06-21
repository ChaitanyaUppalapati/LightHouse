"""Labeled email set for the Arize eval loop (C6).

~25 emails, each tagged with a true_label of "scam" or "legit". The evaluator
(pipeline/evaluator.py) runs the Watcher over these, then uses Claude as a judge
to score each verdict, computes accuracy, and prints the mistakes. This set
doubles as demo content and the basis for the DEMO_MODE cache.

Includes deliberately tricky cases (a real bank fraud alert that LOOKS scammy; a
legit account-locked notice; a borderline subscription renewal) so the eval can
surface real Watcher mistakes to fix — that before/after is the Arize artifact.

Each item: {id, true_label, email{from_name, from_address, subject, body}}.
"""

EVAL_EMAILS = [
    # ---- scams ----------------------------------------------------------
    {"id": "s01", "true_label": "scam", "email": {
        "from_name": "Wells Fargo Security", "from_address": "alerts@wellsfargo-secure-login.com",
        "subject": "Your account is LOCKED — pay $200 to restore access",
        "body": "We locked your account for unusual activity. Pay a $200 verification fee within 24 hours at http://wellsfargo-secure-login.com/restore or it will be closed."}},
    {"id": "s02", "true_label": "scam", "email": {
        "from_name": "Apple Support", "from_address": "no-reply@apple-id-verify.net",
        "subject": "Your Apple ID has been suspended",
        "body": "Verify your identity by confirming your password and card details at http://apple-id-verify.net/unlock or your account will be deleted."}},
    {"id": "s03", "true_label": "scam", "email": {
        "from_name": "Amazon Rewards", "from_address": "rewards@amaz0n-giftcard-claim.com",
        "subject": "Congratulations! You won a $1,000 gift card",
        "body": "Claim your $1,000 Amazon gift card now. Confirm your shipping and bank information at http://amaz0n-giftcard-claim.com/claim. Offer expires today!"}},
    {"id": "s04", "true_label": "scam", "email": {
        "from_name": "IRS Tax Refund", "from_address": "refunds@irs-gov-payments.com",
        "subject": "You are owed a $1,438.00 tax refund — claim now",
        "body": "Confirm your Social Security number and bank account at http://irs-gov-payments.com/claim to receive your refund. Expires in 24 hours."}},
    {"id": "s05", "true_label": "scam", "email": {
        "from_name": "USPS Delivery", "from_address": "tracking@usps-redelivery-fee.com",
        "subject": "Your package #4471 is held — pay redelivery fee",
        "body": "Your package is held pending a $1.99 redelivery fee. Pay at http://usps-redelivery-fee.com to release it."}},
    {"id": "s06", "true_label": "scam", "email": {
        "from_name": "Microsoft Account Team", "from_address": "security@micros0ft-alert.com",
        "subject": "Unusual sign-in activity",
        "body": "We blocked a sign-in. Verify it was you by logging in at http://micros0ft-alert.com/verify with your password."}},
    {"id": "s07", "true_label": "scam", "email": {
        "from_name": "Netflix Billing", "from_address": "billing@netflix-account-update.info",
        "subject": "Your payment was declined — update now",
        "body": "Update your card to avoid cancellation at http://netflix-account-update.info/billing within 48 hours."}},
    {"id": "s08", "true_label": "scam", "email": {
        "from_name": "Grandson Tommy", "from_address": "tommy.help2024@gmail.com",
        "subject": "Grandma I need help",
        "body": "Grandma it's Tommy, I'm in trouble and need $500 wired today. Please don't tell mom and dad. Send it to this account."}},
    {"id": "s09", "true_label": "scam", "email": {
        "from_name": "PayPal", "from_address": "service@paypal-resolution-center.com",
        "subject": "Your account access is limited",
        "body": "We limited your account. Restore access by confirming your login and card at http://paypal-resolution-center.com/resolve."}},
    {"id": "s10", "true_label": "scam", "email": {
        "from_name": "Lottery Commission", "from_address": "winners@global-lotto-payout.org",
        "subject": "Final notice: claim your $4.5M prize",
        "body": "You won the international lottery. To release funds, pay the $350 processing fee and send your bank details to our agent."}},
    {"id": "s11", "true_label": "scam", "email": {
        "from_name": "Geek Squad", "from_address": "renewal@geeksquad-billing-support.com",
        "subject": "Your subscription will auto-renew for $399.99",
        "body": "Your annual plan renews today for $399.99. To cancel, call 1-888-555-0199 and provide your card and bank details."}},
    {"id": "s12", "true_label": "scam", "email": {
        "from_name": "Social Security Admin", "from_address": "alert@ssa-benefits-verify.com",
        "subject": "Your Social Security number is suspended",
        "body": "Your SSN has been suspended due to suspicious activity. Call immediately and confirm your number to avoid legal action."}},

    # ---- legit ----------------------------------------------------------
    {"id": "l01", "true_label": "legit", "email": {
        "from_name": "Walgreens Pharmacy", "from_address": "no-reply@walgreens.com",
        "subject": "Your prescription is ready for pickup",
        "body": "Hello Margaret, your refill is ready at your Walgreens on Main Street. No action needed — stop by when convenient."}},
    {"id": "l02", "true_label": "legit", "email": {
        "from_name": "David Chen", "from_address": "david.chen@gmail.com",
        "subject": "Sunday dinner this weekend?",
        "body": "Hi Mom, are you free for dinner Sunday? I can pick you up around 5. Love, David."}},
    {"id": "l03", "true_label": "legit", "email": {
        "from_name": "Sunrise Senior Living", "from_address": "appointments@sunriseseniorliving.com",
        "subject": "Reminder: checkup appointment Thursday 10am",
        "body": "A friendly reminder of your wellness checkup Thursday at 10:00am with Dr. Patel. Call us to reschedule."}},
    {"id": "l04", "true_label": "legit", "email": {
        "from_name": "Chase", "from_address": "no.reply.alerts@chase.com",
        "subject": "Your statement is ready",
        "body": "Your monthly statement is available. Log in at chase.com to view it. We will never ask for your password by email."}},
    {"id": "l05", "true_label": "legit", "email": {
        "from_name": "Con Edison", "from_address": "billing@coned.com",
        "subject": "Your electricity bill is due June 28",
        "body": "Your balance of $84.20 is due June 28. Pay online at coned.com or by mail. Thank you."}},
    {"id": "l06", "true_label": "legit", "email": {
        "from_name": "Public Library", "from_address": "noreply@nypl.org",
        "subject": "Your hold is ready to pick up",
        "body": "The book you reserved is ready at the 96th Street branch. It will be held for 7 days."}},
    {"id": "l07", "true_label": "legit", "email": {
        "from_name": "Dr. Alvarez Office", "from_address": "office@bayviewclinic.com",
        "subject": "Lab results available in your portal",
        "body": "Your recent lab results are posted to the patient portal. Log in at the address you normally use to view them."}},
    {"id": "l08", "true_label": "legit", "email": {
        "from_name": "Priya Menon", "from_address": "priya.menon@gmail.com",
        "subject": "Calling you after lunch",
        "body": "Hi Mom, I'll call you after lunch today. Hope you slept well. Love you."}},
    {"id": "l09", "true_label": "legit", "email": {
        "from_name": "Costco Wholesale", "from_address": "members@costco.com",
        "subject": "Your membership renews next month",
        "body": "Your annual membership renews on July 15. No action needed — it renews on the card on file. Manage it anytime at costco.com."}},
    {"id": "l10", "true_label": "legit", "email": {
        "from_name": "Verizon", "from_address": "no-reply@verizon.com",
        "subject": "Your bill is now available",
        "body": "Your June bill of $65.00 is ready. View it in the My Verizon app or at verizon.com."}},

    # ---- borderline / tricky (correct label given) ----------------------
    {"id": "b01", "true_label": "legit", "email": {
        "from_name": "Chase Fraud Alert", "from_address": "alerts@chase.com",
        "subject": "Did you make a $312.40 purchase?",
        "body": "We noticed a $312.40 charge at an electronics store. If this was you, no action is needed. If not, call the number on the back of your card. We will never ask for your PIN or password."}},
    {"id": "b02", "true_label": "scam", "email": {
        "from_name": "Chase Fraud Alert", "from_address": "alerts@chase-fraud-dept.com",
        "subject": "Did you make a $312.40 purchase? Verify now",
        "body": "We noticed a $312.40 charge. Verify your identity now by entering your card number, PIN, and online password at http://chase-fraud-dept.com/verify or your account will be frozen."}},
    {"id": "b03", "true_label": "legit", "email": {
        "from_name": "Google", "from_address": "no-reply@accounts.google.com",
        "subject": "Security alert: new sign-in on Windows",
        "body": "A new sign-in to your Google Account on a Windows device. If this was you, you can ignore this email. If not, review your account at the usual myaccount.google.com."}},
]
