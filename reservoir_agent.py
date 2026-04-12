import json
import os
import ast

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import AzureChatOpenAI
from get_llm_model import *

MASTER_RULES = [
    {
        "id": "master_rule_mass_balance_migration",
        "type": "behaviour",
        "text": (
            "In a closed reservoir system, injected fluid migrates toward active pressure sinks "
            "(producers). If a sink is removed via shut-in, redistribution to other sinks is an emergent "
            "reservoir response driven by connectivity, pressure gradients, mobility, and constraints; it "
            "is not operator-controlled. The non-redistributed fraction becomes stranded (pressure "
            "build-up) unless injection is actively curtailed. Therefore, predictions should be reported "
            "as bounded scenarios (0%, intermediate, 100%) representing uncertainty, not control settings."
        ),
    },
    {
        "id": "master_rule_injection_utility",
        "type": "behaviour",
        "text": (
            "The utility of an injection pathway is the ratio of incremental oil recovered per unit of "
            "water injected. Pathways feeding high water-cut producers or lacking production sinks "
            "(stranded) represent zero or negative utility. Optimal system reduction is achieved by "
            "eliminating pathways with the lowest utility score while maintaining required VRR."
        ),
    },
    {
    "id": "master_rule_arbitrage_execution",
    "type": "workflow",
    "text": (
        "Reallocation is an engineering instruction. When 'reallocating' water from a shut-in injector, "
        "the agent must: (1) Identify total available volume from shut-in wells. "
        "(2) Identify target injectors with 'Headroom' and high 'Pathway Utility'. "
        "(3) Provide specific BPD increase values for each target injector. "
        "(4) Run a forecast to ensure the new total rates do not exceed 'System Constraints'."
    )
    },
    
    
    {
        "id": "master_rule_proximity_sweep_dynamics",
        "type": "behaviour",
        "text": (
            "Spatial proximity creates steeper pressure gradients and higher production rates, but "
            "breakthrough time is limited by sweep volume between wells. Shorter distances reduce "
            "cumulative pore volume available for fluid storage, leading to faster water arrival and "
            "accelerated water-cut trends."
        ),
    },
    {
        "id": "master_rule_system_constraints",
        "type": "behaviour",
        "text": (
            "Operational changes must remain within the safety envelope defined by reservoir fracture "
            "pressure and mechanical wellhead limits. Any redistribution of injection that exceeds local "
            "voidage replacement capacity or pressure ceiling can cause system failure or reservoir damage."
        ),
    },
]

 

class ReservoirAgentTools:
    def __init__(self) -> None:
        self.topology = {
            "P1": {"I1": 0.15, "I2": 0.43, "I6": 0.42},
            "P2": {"I1": 1.00},
            "P3": {"I3": 1.00},
            "P4": {"I1": 0.06, "I6": 0.63, "I7": 0.31},
        }
        self.injection_rates = {
            "I1": 743, "I2": 1331, "I3": 1004, "I4": 630,
            "I5": 984, "I6": 1318, "I7": 1146,
        }
        self.production_data = {
            "P1": {"liquid": 420, "water_cut": 0.92},
            "P2": {"liquid": 566, "water_cut": 0.37},
            "P3": {"liquid": 787, "water_cut": 0.79},
            "P4": {"liquid": 413, "water_cut": 0.28},
        }
        self.limits = {
            "I1": 1500, "I2": 1500, "I3": 1200, "I4": 1000, 
            "I5": 1200, "I6": 2000, "I7": 1500,
            "P1": 1000, "P2": 1000, "P3": 1000, "P4": 1000
        }

    def get_system_constraints(self) -> dict:
        """
        Retrieves mechanical and reservoir safety limits (Max BPD).
        
        USE THIS TO: Ensure a proposed reallocation does not exceed 
        mechanical wellhead limits or reservoir fracture pressure.
        """
        return self.limits

    def get_injection_headroom(self) -> dict:
        """
        Calculates available capacity (Max BPD - Current BPD) for every injector.
        
        USE THIS TO: Identify which injectors can safely receive reallocated water 
        without violating system constraints.
        """
        return {
            inj: self.limits.get(inj, 0) - self.injection_rates.get(inj, 0)
            for inj in self.injection_rates
        }

    def get_pathway_utility(self):
        """
        Calculates the 'Value' of injection pathways based on oil production support.
        
        USE THIS TO: Prioritize water reallocation. Pathways feeding 'bad actors' 
        (High WC producers) represent low or negative utility.
        """
        inj_utility = {inj: 0.0 for inj in self.injection_rates}
        for p_id, injectors in self.topology.items():
            p_data = self.production_data.get(p_id, {})
            oil_rate = p_data.get("liquid", 0) * (1 - p_data.get("water_cut", 0))
            for i_id, weight in injectors.items():
                inj_utility[i_id] += (weight * oil_rate)
        return {k: round(v, 2) for k, v in inj_utility.items()}

    def get_current_state(self):
        """
        Retrieves the latest field surveillance snapshot (Rates and Water-Cut).
        
        USE THIS TO: Establish a baseline before diagnosing optimization opportunities.
        """
        return {"injection": self.injection_rates, "production": self.production_data}

    def get_network_topology(self, well_id: str):
        """
        Retrieves hydraulic connectivity weights between wells.
        
        BEHAVIOR: Bidirectional. Returns injectors if P* is provided, returns producers if I* is provided.
        """
        if not isinstance(well_id, str): return {}
        well_id = well_id.strip().upper()
        if well_id.startswith("P"):
            return self.topology.get(well_id, {})
        return {p: conns[well_id] for p, conns in self.topology.items() if well_id in conns}

    def _parse_numeric(self, value):
        if isinstance(value, (int, float)): return float(value)
        if isinstance(value, str):
            raw = value.strip().lower()
            if raw in {"half", "one half"}: return 0.5
            if raw in {"proportional", "auto", "natural", "scenario"}: return "AUTO_SCENARIOS"
            if raw.endswith("%"): return float(raw[:-1]) / 100.0
            try: return float(raw)
            except: pass
        raise ValueError(f"Unsupported numeric value: {value}")

    def _run_with_factor(self, new_inj: dict, active_producers: list, redistribution_factor: float):
        forecasted_support = {p: 0.0 for p in active_producers}
        stranded_volumes = {}
        for inj_id, rate in new_inj.items():
            sinks = {p: self.topology[p][inj_id] for p in active_producers if inj_id in self.topology.get(p, {})}
            if not sinks and rate > 0:
                stranded_volumes[inj_id] = rate
            elif sinks:
                redistributed_rate = rate * redistribution_factor
                total_weight = sum(sinks.values())
                for p, weight in sinks.items():
                    forecasted_support[p] += (weight / total_weight) * redistributed_rate
                non_redist_rate = rate - redistributed_rate
                if non_redist_rate > 0:
                    stranded_volumes[inj_id] = round(stranded_volumes.get(inj_id, 0.0) + non_redist_rate, 2)
        return {
            "forecasted_support_bpd": {k: round(v, 2) for k, v in forecasted_support.items()},
            "stranded_injection_bpd": {k: round(v, 2) for k, v in stranded_volumes.items()},
            "redistribution_factor_applied": round(redistribution_factor, 4),
            "total_reduction_achieved": round(sum(self.injection_rates.values()) - sum(new_inj.values()), 2),
        }

    def run_forecast(self, adjustments: dict):
        """
        Simulate quantitative impact of operational adjustments.
        REQUIRED: You must run this to validate if water reallocation reaches the intended producers.
        """
        if not isinstance(adjustments, dict): return {"error": "adjustments must be a JSON object"}
        new_inj = self.injection_rates.copy()
        active_producers = list(self.production_data.keys())
        redistribution_factor = 1.0
        auto_scenarios = False
        notes = []

        for well, val in adjustments.items():
            if well in {"redistribution_factor", "redistribution_fraction", "redistribute_fraction"}:
                try:
                    parsed = self._parse_numeric(val)
                    if parsed == "AUTO_SCENARIOS": auto_scenarios = True
                    else: redistribution_factor = parsed
                except: redistribution_factor = 1.0
                continue
            if isinstance(well, str) and well.startswith("I"):
                try: new_inj[well] = self._parse_numeric(val)
                except: notes.append(f"invalid injector: {well}")
            elif isinstance(well, str) and well.startswith("P") and str(val).upper() == "SHUT_IN":
                if well in active_producers: active_producers.remove(well)

        if auto_scenarios:
            result = {"scenario_mode": "AUTO_SCENARIOS", "scenarios": {
                "0pct": self._run_with_factor(new_inj, active_producers, 0.0),
                "50pct": self._run_with_factor(new_inj, active_producers, 0.5),
                "100pct": self._run_with_factor(new_inj, active_producers, 1.0)
            }}
        else:
            result = self._run_with_factor(new_inj, active_producers, redistribution_factor)
        if notes: result["notes"] = notes
        return result

    def calculate_injection_utility(self):
        """
        Computes the Utility Score for every injector-producer pathway.
        Formula: (Support_Weight * Producer_Oil_Rate) / Total_Injection
        """
        utility_report = []
        for p_id, injectors in self.topology.items():
            p_data = self.production_data.get(p_id, {})
            oil_rate = p_data.get("liquid", 0) * (1 - p_data.get("water_cut", 0))
            for i_id, weight in injectors.items():
                utility_report.append({
                    "pathway": f"{i_id} -> {p_id}",
                    "utility_score": round(weight * oil_rate, 2),
                    "is_bad_actor": p_data.get("water_cut", 0) > 0.90
                })
        return utility_report 
    
def _require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_llm() -> AzureChatOpenAI:
    return   azure_llm_if()


def build_agent():
    tools_impl = ReservoirAgentTools()

    @tool
    def get_master_rules() -> str:
        """
        Retrieve the canonical first-principles reservoir rules.

        Use this first when solving any operational question so your reasoning is
        grounded in physics (mass balance, utility, sweep dynamics, constraints).

        Returns:
            JSON string with a list of rule objects:
            [{"id": str, "type": "behaviour", "text": str}, ...]
        """
        return json.dumps(MASTER_RULES)

    @tool
    def get_current_state() -> str:
        """
        Get the latest surveillance snapshot used for baseline calculations.

        Use this before recommendations or forecasts that depend on current rates
        and water cut.

        Returns:
            JSON string with:
            {
              "injection": {"I*": rate_bpd, ...},
              "production": {"P*": {"liquid": bpd, "water_cut": fraction}, ...}
            }
        """
        return json.dumps(tools_impl.get_current_state())

    @tool
    def get_network_topology(well_id: str) -> str:
        """
        Get hydraulic connectivity weights for a specific well.

        Input:
            well_id: producer ("P*") or injector ("I*").

        Behavior:
            - If producer is provided, returns connected injectors and weights.
            - If injector is provided, returns connected producers and weights.

        Use this when proving sink migration paths and redistribution logic.

        Returns:
            JSON string mapping connected wells to connectivity weights.
        """
        return json.dumps(tools_impl.get_network_topology(well_id))

    @tool
    def run_forecast(adjustments_json: str) -> str:
        """
        Simulate quantitative impact of operational adjustments.

        Input:
            adjustments_json: JSON object string with well adjustments, for example:
            {"P1":"SHUT_IN"}
            {"I1":500}
            {"P1":"SHUT_IN","redistribution_factor":"half"}
            {"P1":"SHUT_IN","redistribution_factor":"50%"}
            {"P1":"SHUT_IN","redistribution_factor":"proportional"}

        Optional keys:
            redistribution_factor | redistribution_fraction | redistribute_fraction
            - Numeric fraction (0..1), percentage string (e.g., "50%"), or "half".
            - "proportional"/"auto"/"natural"/"scenario" runs:
              0%, 50%, and 100% redistribution scenarios automatically.

        Use this after retrieving topology/state when the question asks "what happens if".

        Returns:
            JSON string with:
            - forecasted_support_bpd
            - stranded_injection_bpd
            - redistribution_factor_applied
            - total_reduction_achieved
            - OR scenario_mode + scenarios when auto scenario mode is requested
            - optional notes / error
        """
        try:
            if isinstance(adjustments_json, str):
                try:
                    adjustments = json.loads(adjustments_json)
                except Exception:
                    # Fallback for Python-like dict strings sometimes emitted by models.
                    adjustments = ast.literal_eval(adjustments_json)
            elif isinstance(adjustments_json, dict):
                adjustments = adjustments_json
            else:
                return json.dumps(
                    {
                        "error": "Invalid adjustments format",
                        "expected": "JSON object string",
                        "received_type": str(type(adjustments_json)),
                    }
                )
            return json.dumps(tools_impl.run_forecast(adjustments))
        except Exception as exc:
            return json.dumps({"error": f"run_forecast_failed: {exc}"})

    system_prompt = """
You are a reservoir engineering reasoning agent.
Objective: answer operational questions from first principles, not FAQ recall.

Reasoning policy:
1. Start from master rules (physics).
2. Pull required evidence using tools (state, topology, forecast).
3. Synthesize clear quantitative guidance.
4. If data is missing, state exactly what is missing before concluding.
5. Assume that injectors not explicitly listed as support of any producer are fully stranded.
 
Always explain: (a) governing rule used, (b) tool evidence used, (c) recommendation.

Critical constraint:

- If scenarios are shown (0%, partial, 100%), label them as assumptions for decision support.
- Recommendations must be operational actions the user can actually take
  (e.g., change injector rates, shut-in wells, surveillance/pressure monitoring)
- Treat redistribution as uncertain reservoir behavior.
  
"""

    return create_agent(
        model=build_llm(),
        tools=[get_master_rules, get_current_state, get_network_topology, run_forecast],
        system_prompt=system_prompt,
    )


def ask(agent, user_text: str) -> str:
    response = agent.invoke({"messages": [{"role": "user", "content": user_text}]})
    return response["messages"][-1].content


def main() -> None:
    load_dotenv()
    agent = build_agent()
    print("Reservoir Agent ready. Type 'exit' to quit.")
    while True:
        print(80 * '-')
        question = input("\nYou: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        print(f"\nAgent: {ask(agent, question)}")
        print(80 * '-')

if __name__ == "__main__":
    main()
