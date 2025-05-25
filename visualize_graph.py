import os
import sys
import matplotlib.pyplot as plt
import networkx as nx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_travel_agent_graph():
    states = [
        "START",
        "CHECK_GUARDRAIL",
        "UNDERSTAND_REQUEST",
        "ASK_DESTINATION",
        "COLLECT_DETAILS",
        "GENERATE_PLAN",
        "REFINE_PLAN", 
        "REGISTER_CALENDAR",
        "VIEW_CALENDAR",
        "MODIFY_CALENDAR",
        "DELETE_CALENDAR",
        "END"
    ]
    
    # state_handlers.py의 실제 구현을 반영한 워크플로우
    edges = [
        # 시작과 가드레일
        ("START", "CHECK_GUARDRAIL"),
        ("CHECK_GUARDRAIL", "UNDERSTAND_REQUEST"),
        ("CHECK_GUARDRAIL", "END"),  # 가드레일 위반시
        
        # 기본 플로우
        ("UNDERSTAND_REQUEST", "ASK_DESTINATION"),
        ("UNDERSTAND_REQUEST", "COLLECT_DETAILS"),
        ("UNDERSTAND_REQUEST", "GENERATE_PLAN"),
        ("UNDERSTAND_REQUEST", "VIEW_CALENDAR"),
        ("UNDERSTAND_REQUEST", "END"),
        
        # 목적지 확인 후
        ("ASK_DESTINATION", "COLLECT_DETAILS"),
        ("ASK_DESTINATION", "UNDERSTAND_REQUEST"),
        ("ASK_DESTINATION", "END"),
        
        # 세부정보 수집 후
        ("COLLECT_DETAILS", "GENERATE_PLAN"),
        ("COLLECT_DETAILS", "UNDERSTAND_REQUEST"),
        ("COLLECT_DETAILS", "END"),
        
        # 계획 생성 후
        ("GENERATE_PLAN", "REFINE_PLAN"),
        ("GENERATE_PLAN", "REGISTER_CALENDAR"),
        ("GENERATE_PLAN", "UNDERSTAND_REQUEST"),
        ("GENERATE_PLAN", "END"),
        
        # 계획 수정
        ("REFINE_PLAN", "REGISTER_CALENDAR"),
        ("REFINE_PLAN", "GENERATE_PLAN"),
        ("REFINE_PLAN", "COLLECT_DETAILS"),
        ("REFINE_PLAN", "UNDERSTAND_REQUEST"),
        ("REFINE_PLAN", "END"),
        
        # 캘린더 관련
        ("REGISTER_CALENDAR", "VIEW_CALENDAR"),
        ("REGISTER_CALENDAR", "MODIFY_CALENDAR"),
        ("REGISTER_CALENDAR", "UNDERSTAND_REQUEST"),
        ("REGISTER_CALENDAR", "END"),
        
        ("VIEW_CALENDAR", "MODIFY_CALENDAR"),
        ("VIEW_CALENDAR", "DELETE_CALENDAR"),
        ("VIEW_CALENDAR", "UNDERSTAND_REQUEST"),
        ("VIEW_CALENDAR", "END"),
        
        ("MODIFY_CALENDAR", "VIEW_CALENDAR"),
        ("MODIFY_CALENDAR", "UNDERSTAND_REQUEST"),
        ("MODIFY_CALENDAR", "END"),
        
        ("DELETE_CALENDAR", "UNDERSTAND_REQUEST"),
        ("DELETE_CALENDAR", "END"),
        
        # 모든 상태에서 다시 요청 이해로 돌아갈 수 있음
        ("ASK_DESTINATION", "UNDERSTAND_REQUEST"),
        ("COLLECT_DETAILS", "UNDERSTAND_REQUEST"),
        ("GENERATE_PLAN", "UNDERSTAND_REQUEST"),
        ("REFINE_PLAN", "UNDERSTAND_REQUEST"),
        ("REGISTER_CALENDAR", "UNDERSTAND_REQUEST"),
        ("VIEW_CALENDAR", "UNDERSTAND_REQUEST"),
        ("MODIFY_CALENDAR", "UNDERSTAND_REQUEST"),
        ("DELETE_CALENDAR", "UNDERSTAND_REQUEST")
    ]
    
    G = nx.DiGraph()
    
    for node in states:
        G.add_node(node)
    
    for source, target in edges:
        G.add_edge(source, target)
    
    return G

def visualize_travel_agent_graph():
    G = create_travel_agent_graph()
    
    # 첫 번째 그래프 - 계층적 레이아웃
    plt.figure(figsize=(16, 12))
    
    # 수동으로 위치 설정하여 더 명확한 플로우 표현
    pos = {
        "START": (0, 10),
        "CHECK_GUARDRAIL": (0, 9),
        "UNDERSTAND_REQUEST": (0, 7),
        "ASK_DESTINATION": (-3, 6),
        "COLLECT_DETAILS": (0, 5),
        "GENERATE_PLAN": (0, 3),
        "REFINE_PLAN": (-2, 2),
        "REGISTER_CALENDAR": (2, 2),
        "VIEW_CALENDAR": (-4, 1),
        "MODIFY_CALENDAR": (-2, 0),
        "DELETE_CALENDAR": (-4, -1),
        "END": (4, 0)
    }
    
    # 노드 색상 설정 (기능별 그룹화)
    node_colors = {
        "START": "lightgreen",
        "CHECK_GUARDRAIL": "orange",
        "UNDERSTAND_REQUEST": "lightblue", 
        "ASK_DESTINATION": "lightyellow",
        "COLLECT_DETAILS": "lightyellow",
        "GENERATE_PLAN": "lightcoral",
        "REFINE_PLAN": "lightcoral",
        "REGISTER_CALENDAR": "lightpink",
        "VIEW_CALENDAR": "lightcyan",
        "MODIFY_CALENDAR": "lightcyan",
        "DELETE_CALENDAR": "lightcyan",
        "END": "lightgray"
    }
    
    colors = [node_colors[node] for node in G.nodes()]
    
    # 노드 크기를 중요도에 따라 조정
    node_sizes = {
        "START": 3000,
        "CHECK_GUARDRAIL": 3500,
        "UNDERSTAND_REQUEST": 4500,
        "ASK_DESTINATION": 3500,
        "COLLECT_DETAILS": 3500,
        "GENERATE_PLAN": 4000,
        "REFINE_PLAN": 3500,
        "REGISTER_CALENDAR": 3500,
        "VIEW_CALENDAR": 3000,
        "MODIFY_CALENDAR": 3000,
        "DELETE_CALENDAR": 3000,
        "END": 3000
    }
    
    sizes = [node_sizes[node] for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.9)
    nx.draw_networkx_edges(G, pos, arrowsize=15, arrowstyle='->', 
                          edge_color='gray', alpha=0.6, width=1.5)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold")
    
    plt.title("Travel Agent Complete Workflow with Guardrail", fontsize=18, fontweight='bold', pad=20)
    plt.axis('off')
    
    # 범례 추가
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', 
                  markersize=10, label='Start'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                  markersize=10, label='Security Check'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', 
                  markersize=10, label='Understanding'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightyellow', 
                  markersize=10, label='Information Gathering'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightcoral', 
                  markersize=10, label='Plan Generation/Refinement'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightpink', 
                  markersize=10, label='Calendar Registration'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightcyan', 
                  markersize=10, label='Calendar Management'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgray', 
                  markersize=10, label='End')
    ]
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))
    
    plt.tight_layout()
    plt.savefig("travel_agent_workflow.png", dpi=300, bbox_inches='tight')
    print("Travel agent complete workflow graph saved as 'travel_agent_workflow.png'")
    
    # 두 번째 그래프 - 기능별 그룹화된 레이아웃
    try:
        plt.figure(figsize=(14, 10))
        
        # 기능별로 그룹화된 위치 설정
        grouped_pos = {
            # 시작 및 보안
            "START": (0, 8),
            "CHECK_GUARDRAIL": (0, 7),
            
            # 핵심 대화 플로우
            "UNDERSTAND_REQUEST": (0, 5),
            "ASK_DESTINATION": (-2, 4),
            "COLLECT_DETAILS": (0, 3),
            
            # 계획 관련
            "GENERATE_PLAN": (-1, 1),
            "REFINE_PLAN": (1, 1),
            
            # 캘린더 관련
            "REGISTER_CALENDAR": (3, 2),
            "VIEW_CALENDAR": (4, 1),
            "MODIFY_CALENDAR": (5, 0),
            "DELETE_CALENDAR": (4, -1),
            
            # 종료
            "END": (2, -2)
        }
        
        nx.draw(G, grouped_pos, with_labels=True, node_color=colors, 
                node_size=sizes, font_size=8, font_weight="bold",
                arrows=True, arrowsize=15, edge_color='gray', 
                alpha=0.8, width=1.5)
        
        plt.title("Travel Agent Workflow (Grouped by Function)", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig("travel_agent_workflow_grouped.png", dpi=300, bbox_inches='tight')
        print("Grouped layout graph saved as 'travel_agent_workflow_grouped.png'")
    except Exception as e:
        print(f"Could not create grouped layout: {str(e)}")

if __name__ == "__main__":
    visualize_travel_agent_graph() 