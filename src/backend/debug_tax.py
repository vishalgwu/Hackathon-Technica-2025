from src.backend.agents.tax_agent import TaxAgent

if __name__ == "__main__":
    agent = TaxAgent()

    tx = {
        "description": "UBER TRIP NEW YORK",
        "amount": 45.90,
        "merchant": "UBER"
    }

    result = agent.analyze_transaction(tx)
    print(result)
