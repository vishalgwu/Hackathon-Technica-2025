from typing import Any, Dict, List

# Import agents
from .agents.extraction_agent import ExtractionAgent
from .agents.tax_agent import TaxDeductionAgent
from .agents.compliance_agent import ComplianceAgent
from .agents.summary_agent import SummaryAgent


# ==============================================================
#   DEFINE ORCHESTRATOR CLASS
# ==============================================================

class ExpenseOrchestrator:
    """
    Runs the full multi-agent pipeline on a list of receipts.
    Flow:
        raw_receipts -> Extraction -> Tax -> Compliance -> Summary
    """

    def __init__(self, marginal_tax_rate: float = 0.22):
        self.extraction_agent = ExtractionAgent()
        self.tax_agent = TaxDeductionAgent(marginal_tax_rate=marginal_tax_rate)
        self.compliance_agent = ComplianceAgent()
        self.summary_agent = SummaryAgent()

    def run(self, raw_receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            "raw_receipts": raw_receipts,
            "extracted": [],
            "deductions": [],
            "compliance_flags": [],
            "summary": {},
        }

        # Run agents
        state = self.extraction_agent.run(state)
        state = self.tax_agent.run(state)
        state = self.compliance_agent.run(state)
        state = self.summary_agent.run(state)

        return state


# ==============================================================
#   MAIN BLOCK FOR MANUAL TESTING
# ==============================================================

if __name__ == "__main__":
    from src.backend.load_structured import load_structured_receipts
    from pprint import pprint

    print("\nLoading structured receipts...")
    raw_receipts = load_structured_receipts()
    print("\n=== RAW RECEIPTS LOADED FROM PARQUET ===")
    from pprint import pprint

    pprint(raw_receipts)

    if not raw_receipts:
        print("❌ No structured receipts found in data/structured/.")
    else:
        print(f"Loaded {len(raw_receipts)} receipts")

        orchestrator = ExpenseOrchestrator(marginal_tax_rate=0.24)
        final_state = orchestrator.run(raw_receipts)

        print("\n=== SUMMARY ===")
        pprint(final_state["summary"])

        print("\n=== COMPLIANCE FLAGS ===")
        pprint(final_state["compliance_flags"])

        print("\n=== DEDUCTIONS ===")
        pprint(final_state["deductions"])
