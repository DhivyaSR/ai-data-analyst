# chat.py

import agent

history = None

print("Ask about sales (type 'quit' to exit)")
while True:
    q = input("\nYou: ")
    if q.lower() == "quit":
        break
    answer, data = agent.run_agent(q, history)
    print("Analyst:", answer)