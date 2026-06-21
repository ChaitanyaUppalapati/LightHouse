"""Harder adversarial eval set for the before/after loop (C6).

The base set (eval_emails.py) is easy and the Watcher aces it. These are the
genuinely tricky cases that stress a strong classifier in both directions:

  - false-positive bait: LEGIT mail that looks scary (real bank fraud alerts,
    password resets the user asked for, real overdue bills with urgent language).
    A trigger-happy Watcher over-flags these as scams.
  - false-negative bait: SUBTLE scams with a professional tone and few red flags
    (vendor ACH-change / invoice fraud, shared-document phishing). A Watcher that
    relies on obvious cues lets these through.

The point is to find real Watcher mistakes the Phoenix eval can surface, so the
prompt fix moves the accuracy number (the before/after artifact).
"""

EVAL_EMAILS_HARD = [
    # ---- legit but scary (false-positive bait) --------------------------
    {"id": "h01", "true_label": "legit", "email": {
        "from_name": "Chase Fraud Alert", "from_address": "alerts@chase.com",
        "subject": "Action may be required: did you authorize $640.00 at BestBuy?",
        "body": "We're confirming a $640.00 purchase on your card ending 4412. If this was you, no action is needed. If not, call the number on the back of your card. We will never ask for your password, PIN, or full card number by email or phone."}},
    {"id": "h02", "true_label": "legit", "email": {
        "from_name": "Google", "from_address": "no-reply@accounts.google.com",
        "subject": "Security alert: new sign-in on a Windows device",
        "body": "Your Google Account was just signed in to on a new Windows device. If this was you, you don't need to do anything. If not, review activity at myaccount.google.com using your usual bookmark."}},
    {"id": "h03", "true_label": "legit", "email": {
        "from_name": "PG&E", "from_address": "billing@pge.com",
        "subject": "Final notice: your past-due balance of $212.45 is due in 3 days",
        "body": "Your account is past due. To avoid service interruption, pay your $212.45 balance by June 24. Pay online at pge.com or by phone. This is your final reminder before disconnection."}},
    {"id": "h04", "true_label": "legit", "email": {
        "from_name": "Okta", "from_address": "noreply@okta.com",
        "subject": "Your password reset request",
        "body": "We received a request to reset your password. Use the verification code 882140, valid for 10 minutes. If you didn't request this, you can ignore this email and your password will stay the same."}},
    {"id": "h05", "true_label": "legit", "email": {
        "from_name": "IRS", "from_address": "no-reply@irs.gov",
        "subject": "Your IRS account: identity verification reminder",
        "body": "To finish setting up your online account at irs.gov, complete identity verification at your convenience. The IRS will never email you to demand immediate payment or ask for card numbers."}},
    {"id": "h06", "true_label": "legit", "email": {
        "from_name": "Bank of America", "from_address": "onlinebanking@bankofamerica.com",
        "subject": "We've temporarily locked your card for your protection",
        "body": "We noticed unusual activity and temporarily locked your debit card. To unlock it, sign in to the Bank of America app or call the number on the back of your card. We will not ask for your PIN."}},
    {"id": "h07", "true_label": "legit", "email": {
        "from_name": "Amazon", "from_address": "auto-confirm@amazon.com",
        "subject": "Your order will arrive late — refund available",
        "body": "Your recent order is delayed. You can request a refund or wait for delivery in Your Orders on amazon.com. No need to share any payment details — just use your account."}},

    # ---- subtle scams (false-negative bait) -----------------------------
    {"id": "h08", "true_label": "scam", "email": {
        "from_name": "Maria Lopez, Accounts Payable", "from_address": "m.lopez@vendor-billing-update.com",
        "subject": "Updated banking details for your next payment",
        "body": "Hi, following our recent process change, please update our remittance details for the upcoming invoice. Our new ACH account is attached. Kindly confirm once your records are updated so there's no delay. Thank you, Maria."}},
    {"id": "h09", "true_label": "scam", "email": {
        "from_name": "DocuSign", "from_address": "dse@docu-sign-secure.com",
        "subject": "Completed: Please review and sign — Agreement_0624.pdf",
        "body": "A document has been shared with you for signature. Review and sign the agreement using the secure link below. This link will expire in 24 hours."}},
    {"id": "h10", "true_label": "scam", "email": {
        "from_name": "HR Benefits", "from_address": "benefits@hr-portal-verify.com",
        "subject": "Confirm your direct deposit before payroll closes",
        "body": "Open enrollment requires you to re-confirm your direct deposit information before this Friday's payroll run. Log in to the benefits portal with the link below and verify your bank account to avoid a delayed paycheck."}},
    {"id": "h11", "true_label": "scam", "email": {
        "from_name": "Norton", "from_address": "support@norton-billing-team.com",
        "subject": "Receipt: your Norton 360 renewal — $89.99",
        "body": "Thank you for renewing Norton 360 for $89.99. If you did not authorize this charge, call our billing support line at 1-855-0142 to cancel and receive a refund. Have your card ready for verification."}},
    {"id": "h12", "true_label": "scam", "email": {
        "from_name": "Coinbase", "from_address": "no-reply@coinbase-secure-alerts.com",
        "subject": "Withdrawal request received",
        "body": "We received a request to withdraw 0.42 BTC from your account. If you did not make this request, cancel it immediately using the link below and reset your security settings."}},
    {"id": "h13", "true_label": "scam", "email": {
        "from_name": "Property Manager", "from_address": "leasing@parkview-residences.net",
        "subject": "June rent — new payment portal",
        "body": "We've switched payment providers. Please submit June rent through our new portal at the link below. To avoid a late fee, complete payment by the 5th. Let us know if you have any trouble logging in."}},

    # ---- a couple of clear anchors (sanity) -----------------------------
    {"id": "h14", "true_label": "scam", "email": {
        "from_name": "Apple Support", "from_address": "no-reply@apple-id-verify.net",
        "subject": "Your Apple ID has been suspended",
        "body": "Verify your identity by confirming your password and card details at http://apple-id-verify.net/unlock or your account will be deleted."}},
    {"id": "h15", "true_label": "legit", "email": {
        "from_name": "Priya Menon", "from_address": "priya.menon@gmail.com",
        "subject": "Lunch Sunday?",
        "body": "Hi Mom, free for lunch Sunday? I'll pick you up at noon. Love, Priya."}},
]
