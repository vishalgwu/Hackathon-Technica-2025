from src.backend.agents.compliance_agent import ComplianceAgent


if __name__ == "__main__":
    agent = ComplianceAgent()

    sample_tx = {
        "description": "ATM CASH WITHDRAWAL - DOWNTOWN BRANCH",
        "merchant": "CHASE ATM",
        "amount": 1200.00,
    }

    result = agent.assess_transaction(sample_tx)
    print("Compliance result:")
    print(result)
