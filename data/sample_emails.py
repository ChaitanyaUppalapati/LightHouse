"""Built-in fake emails for the mock signal feed (task K2).

Six emails the Watcher (Chaitanya's C1) classifies against: three obvious scams
and three normal messages. Each becomes the `payload` of an email Signal served
by GET /signals/next. Kept here so the list is easy to read and extend without
touching the feed logic in main.py.

Each entry is a plain dict — the raw email as observed, never trusted or
pre-judged (the judgment is the Watcher's job, not the feed's).
"""

# label is for our own readability/tests only; it is NOT sent as a verdict.
SAMPLE_EMAILS = [
    # --- scams -------------------------------------------------------------
    {
        "label": "scam",
        "from_name": "Wells Fargo Security",
        "from_address": "alerts@wellsfargo-secure-login.com",
        "subject": "Your account is LOCKED — pay $200 to restore access",
        "body": (
            "Dear Customer, we detected unusual activity and locked your account. "
            "To restore access you must pay a $200 verification fee within 24 hours "
            "or your account will be permanently closed. Click here to pay now: "
            "http://wellsfargo-secure-login.com/restore"
        ),
    },
    {
        "label": "scam",
        "from_name": "Apple Support",
        "from_address": "no-reply@apple-id-verify.net",
        "subject": "Your Apple ID has been suspended",
        "body": (
            "We have locked your Apple ID due to a security concern. Verify your "
            "identity immediately by confirming your password and card details at "
            "http://apple-id-verify.net/unlock or your account will be deleted."
        ),
    },
    {
        "label": "scam",
        "from_name": "Amazon Rewards",
        "from_address": "rewards@amaz0n-giftcard-claim.com",
        "subject": "Congratulations! You won a $1,000 gift card",
        "body": (
            "You have been selected to receive a $1,000 Amazon gift card! "
            "To claim your prize, confirm your shipping and bank information here: "
            "http://amaz0n-giftcard-claim.com/claim. Offer expires today!"
        ),
    },
    # --- normal ------------------------------------------------------------
    {
        "label": "normal",
        "from_name": "Walgreens Pharmacy",
        "from_address": "no-reply@walgreens.com",
        "subject": "Your prescription is ready for pickup",
        "body": (
            "Hello Margaret, your prescription refill is ready for pickup at your "
            "Walgreens on Main Street. Store hours are 9am-9pm. No action needed — "
            "just stop by when convenient."
        ),
    },
    {
        "label": "normal",
        "from_name": "David Chen",
        "from_address": "david.chen@gmail.com",
        "subject": "Sunday dinner this weekend?",
        "body": (
            "Hi Mom, hope you're doing well! Are you free for dinner on Sunday? "
            "I can pick you up around 5. Let me know. Love, David."
        ),
    },
    {
        "label": "normal",
        "from_name": "Sunrise Senior Living",
        "from_address": "appointments@sunriseseniorliving.com",
        "subject": "Reminder: checkup appointment Thursday 10am",
        "body": (
            "This is a friendly reminder of your wellness checkup on Thursday at "
            "10:00am with Dr. Patel. Please call us if you need to reschedule."
        ),
    },
]
