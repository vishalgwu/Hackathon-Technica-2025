from src.backend.agents.summary_agent import SummaryAgent


if __name__ == "__main__":
    agent = SummaryAgent()

    sample_transactions = [
        {
            "date": "2024-10-01",
            "description": "UBER TRIP NYC",
            "merchant": "UBER",
            "amount": -23.45,
        },
        {
            "date": "2024-10-02",
            "description": "WHOLE FOODS MARKET",
            "merchant": "WHOLE FOODS",
            "amount": -85.20,
        },
        {
            "date": "2024-10-03",
            "description": "RENT PAYMENT",
            "merchant": "APARTMENTS LLC",
            "amount": -1500.00,
        },
        {
            "date": "2024-11-01",
            "description": "BEST BUY ELECTRONICS",
            "merchant": "BEST BUY",
            "amount": -799.99,
        },
        {
            "date": "2024-11-02",
            "description": "PAYROLL DEPOSIT",
            "merchant": "EMPLOYER INC",
            "amount": 3200.00,
        },
        {
            "date": "2024-11-05",
            "description": "ATM CASH WITHDRAWAL",
            "merchant": "CHASE ATM",
            "amount": -1200.00,
        },
    ]

    result = agent.summarize(sample_transactions)

    print("Monthly totals:")
    print(result["monthly_totals"])

    print("\nCategory totals:")
    print(result["category_totals"])

    print("\nMerchant totals:")
    print(result["merchant_totals"])

    print("\nUnusual transactions:")
    print(result["unusual_transactions"])

    print("\nSummary text:")
    print(result["summary_text"])
