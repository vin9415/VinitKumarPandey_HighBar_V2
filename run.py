from src.orchestrator.orchestrator import Orchestrator

def main():
    orch = Orchestrator()
    # Replace the task description with whatever you want the system to do
    user_task = "Analyze recent sales and propose 3 improvements"
    result = orch.run(user_task)
    print("\n=== FINAL RESULT ===")
    for k, v in result.items():
        print(f"{k}:\n{v}\n")

if __name__ == "__main__":
    main()
