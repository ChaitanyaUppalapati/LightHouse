// S5 — fake online banking data. The page at /bank must look real: in the demo the
// family DENIES the payment, so it never completes, but C5's pay action opens this page
// (MOCK_BANK_URL) and would fill the form. Keep it believable.
export const ACCOUNT = {
  bankName: "Harbor Federal",
  holder: "Margaret Doyle",
  type: "Everyday Checking",
  number: "•••• 4471",
  balance: 8240.16,
};

export const TRANSACTIONS = [
  { id: "tx_1", name: "Social Security Administration", memo: "Monthly benefit", date: "Jun 18", amount: 1742.0 },
  { id: "tx_2", name: "Bayview Pharmacy", memo: "Prescription", date: "Jun 17", amount: -34.2 },
  { id: "tx_3", name: "Green Valley Grocery", memo: "Card purchase", date: "Jun 16", amount: -82.55 },
  { id: "tx_4", name: "City Water & Power", memo: "Utility bill", date: "Jun 14", amount: -96.4 },
  { id: "tx_5", name: "Priya Menon", memo: "Thanks mom!", date: "Jun 12", amount: 50.0 },
];

export const usd = (n) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD" });
