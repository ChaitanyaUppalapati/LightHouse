// S4 — fake inbox the browser agent (Browserbase + Stagehand) operates: it opens this
// page, clicks the flagged scam email, and clicks "Move to Quarantine". Keep senders/
// subjects realistic and the scams obvious so the demo reads clearly.
export const INBOX_EMAILS = [
  {
    id: "em_securebank",
    sender: "SecureBank Support",
    email: "billing-alert@secure-bank-help.com",
    subject: "URGENT: Your account is locked",
    preview: "Pay a $200 verification fee within 24 hours to unlock your account.",
    body: "Dear Customer, your bank account has been LOCKED due to suspicious activity. To unlock it immediately, pay a $200 verification fee using the link below. Failure to act within 24 hours will result in permanent closure. SecureBank Support.",
    time: "9:14 AM",
    scam: true,
    folder: "inbox",
  },
  {
    id: "em_clinic",
    sender: "Bayview Clinic",
    email: "appointments@bayviewclinic.com",
    subject: "Appointment reminder for Thursday",
    preview: "A friendly reminder of your check-up this Thursday at 10:00 AM.",
    body: "Hello Margaret, this is a friendly reminder of your check-up this Thursday at 10:00 AM with Dr. Alvarez. Please bring your current list of medications. Call us anytime if you need to reschedule.",
    time: "8:30 AM",
    scam: false,
    folder: "inbox",
  },
  {
    id: "em_priya",
    sender: "Priya",
    email: "priya.menon@gmail.com",
    subject: "Lunch on Sunday?",
    preview: "Hi Mom, are you free for lunch this Sunday? I can pick you up.",
    body: "Hi Mom, are you free for lunch this Sunday? I can pick you up around noon. Let me know what you feel like eating. Love, Priya.",
    time: "Yesterday",
    scam: false,
    folder: "inbox",
  },
  {
    id: "em_lottery",
    sender: "Lucky Winner Rewards",
    email: "prizes@lucky-winner-rewards.net",
    subject: "You have WON a $1,000 gift card!",
    preview: "Congratulations! Confirm your details now to claim your prize.",
    body: "CONGRATULATIONS! You have been selected to receive a $1,000 gift card. To claim your prize, confirm your full name, home address, and card number at the link below within 48 hours.",
    time: "Yesterday",
    scam: true,
    folder: "inbox",
  },
];
