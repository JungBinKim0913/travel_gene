import os
import sys
import matplotlib.pyplot as plt
import networkx as nx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_travel_agent_graph():
    states = [
        "UNDERSTAND_REQUEST",
        "ASK_DESTINATION",
        "COLLECT_DETAILS",
        "GENERATE_PLAN",
        "REFINE_PLAN", 
        "REGISTER_CALENDAR",
        "END"
    ]
    
    edges = [
        ("UNDERSTAND_REQUEST", "ASK_DESTINATION"),
        ("UNDERSTAND_REQUEST", "COLLECT_DETAILS"),
        ("UNDERSTAND_REQUEST", "GENERATE_PLAN"),
        ("UNDERSTAND_REQUEST", "REFINE_PLAN"),
        ("UNDERSTAND_REQUEST", "REGISTER_CALENDAR"),
        ("UNDERSTAND_REQUEST", "END"),
        ("ASK_DESTINATION", "END"),
        ("COLLECT_DETAILS", "END"),
        ("GENERATE_PLAN", "END"),
        ("REFINE_PLAN", "END"),
        ("REGISTER_CALENDAR", "END")
    ]
    
    G = nx.DiGraph()
    
    for node in states:
        G.add_node(node)
    
    for source, target in edges:
        G.add_edge(source, target)
    
    return G

def visualize_travel_agent_graph():
    G = create_travel_agent_graph()
    
    plt.figure(figsize=(12, 8))
    
    pos = nx.spring_layout(G, seed=42)
    
    nx.draw_networkx_nodes(G, pos, node_color="skyblue", node_size=3000)
    
    nx.draw_networkx_edges(G, pos, arrowsize=20, arrowstyle='->')
    
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")
    
    plt.title("Travel Agent Workflow", fontsize=15)
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig("travel_agent_workflow.png")
    print("Travel agent workflow graph saved as 'travel_agent_workflow.png'")
    
    try:
        plt.figure(figsize=(12, 8))
        
        try:
            pos = nx.kamada_kawai_layout(G, scale=2.0)
        except:
            pos = nx.shell_layout(G, scale=2.0)
        
        nx.draw(G, pos, with_labels=True, node_color="lightgreen", 
                node_size=3000, font_size=10, font_weight="bold",
                arrows=True, arrowsize=20)
        
        plt.title("Travel Agent Workflow (Alternative Layout)", fontsize=15)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig("travel_agent_workflow_alt.png")
        print("Alternative layout graph saved as 'travel_agent_workflow_alt.png'")
    except Exception as e:
        print(f"Could not create alternative layout: {str(e)}")

if __name__ == "__main__":
    visualize_travel_agent_graph() 