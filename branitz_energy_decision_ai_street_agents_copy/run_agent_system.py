# run_agent_system.py
from adk.api.adk import ADK
from agents import (
    EnergyPlannerAgent,
    CentralHeatingAgent,
    DecentralizedHeatingAgent,
    ComparisonAgent,
    DataExplorerAgent,
)

# Initialize the ADK. This manages agents and tool calls.
adk = ADK()


def main():
    """The main conversation loop for orchestrating the agents."""

    print("🚀 Starting Branitz Energy Planning Assistant...")
    print("You are now talking to the EnergyPlannerAgent. Here are some examples:")
    print("• 'analyze district heating for Parkstraße'")
    print("• 'compare scenarios for Kastenstraße'")
    print("• 'show available streets'")
    print("• 'list results'")
    print("• 'exit' or 'quit'")

    while True:
        try:
            user_input = input("\n🎯 Your request: ")
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Thank you for using the Branitz Energy Planning Assistant!")
                break

            # --- Step 1: Delegation by the Planner Agent ---
            print("\n🤔 Planner Agent is thinking...")
            planner_response = adk.run(EnergyPlannerAgent, user_input)

            delegate_agent_name = planner_response.agent_response.strip().upper()

            agent_map = {
                "CHA": CentralHeatingAgent,
                "DHA": DecentralizedHeatingAgent,
                "CA": ComparisonAgent,
                "DEA": DataExplorerAgent,
            }

            if delegate_agent_name in agent_map:
                active_agent = agent_map[delegate_agent_name]
                print(f"🎯 Planner delegated to {active_agent.config.name}.")
            else:
                print(f"❌ Planner response was unclear: '{planner_response.agent_response}'")
                print("Please try again with a clearer request.")
                continue

            # --- Step 2: Execution by the Specialist Agent ---
            print(f"⚡ {active_agent.config.name} is executing the complete task...")
            final_response = adk.run(active_agent, user_input)

            print(
                f"\n✅ Request complete! Here is the final summary from {active_agent.config.name}:"
            )
            print("-" * 60)
            print(final_response.agent_response)
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            import traceback

            traceback.print_exc()
            print("Please try again.")


if __name__ == "__main__":
    main()
