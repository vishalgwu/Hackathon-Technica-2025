from src.backend.agents import ClassificationAgent


if __name__ == "__main__":
    agent = ClassificationAgent()

    sample_tx = {
        "description": "UBER *TRIP 123 NYC",
        "merchant": "UBER",
        "amount": 23.45,
    }

    category = agent.classify_transaction(sample_tx)
    print("Category 1:", category)

    sample_tx2 = {
        "description": "CHASE DEBIT CARD PURCHASE BEST BUY #1234",
        "merchant": "BEST BUY",
        "amount": 499.99,
    }

    category2 = agent.classify_transaction(sample_tx2)
    print("Category 2:", category2)
