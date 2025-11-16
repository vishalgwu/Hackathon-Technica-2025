from src.backend.agents.dispatcher_agent import DispatcherAgent


if __name__ == "__main__":
    agent = DispatcherAgent()

    # Full transaction list (for summary)
    transactions = [
        {"date": "2024-10-01", "description": "UBER TRIP", "merchant": "UBER", "amount": -23.45},
        {"date": "2024-10-02", "description": "WHOLE FOODS", "merchant": "WHOLE FOODS", "amount": -85.20},
        {"date": "2024-10-03", "description": "RENT PAYMENT", "merchant": "APARTMENTS", "amount": -1500.00},
        {"date": "2024-11-01", "description": "BEST BUY ELECTRONICS", "merchant": "BEST BUY", "amount": -799.99},
        {"date": "2024-11-02", "description": "PAYROLL", "merchant": "EMPLOYER", "amount": 3200.00},
    ]

    # Single transaction for tax/compliance
    tx = {"description": "ATM WITHDRAWAL", "merchant": "CHASE ATM", "amount": 1200.00}

    # Try different queries
    queries = [
        "What did I spend last month?",
        "Is this transaction suspicious?",
        "Can I deduct this expense?",
        "What category is this charge?",
        "What did I spend last month and is this ATM charge risky?",
    ]

    for q in queries:
        print("\n\nQUERY:", q)
        result = agent.analyze(
            query=q,
            transactions=transactions,
            single_tx=tx,
        )
        print(result)
