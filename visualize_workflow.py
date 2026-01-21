"""Generate a visualization of the LangGraph workflow."""
from main import build_workflow

def main():
    """Generate workflow diagram as PNG."""
    app = build_workflow()
    
    # Generate PNG using Mermaid (built-in, no external dependencies)
    png_data = app.get_graph().draw_mermaid_png()
    
    with open("assets/workflow.png", "wb") as f:
        f.write(png_data)
    
    print("✓ Workflow diagram saved to assets/workflow.png")

if __name__ == "__main__":
    main()
