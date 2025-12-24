# System Design Patterns

## AI Design Automation Pipeline

This document outlines the usage patterns for the AI-driven design and UI/UX generation pipeline.

### 21st.dev Magic MCP

The 21st.dev Magic MCP is a tool that allows you to generate UI components from natural language prompts.

**Usage:**

1.  **Open the Command Palette:** In your editor, open the command palette (e.g., `Cmd+Shift+P` in VS Code).
2.  **Run a prompt:** Type a prompt to generate a UI component. For example:
    `/ui create a modern login form`
3.  **Select a component:** The Magic MCP will return a list of components. Select the one that best fits your needs.
4.  **The component will be added to your project.**

**API Key Management:**

The 21st.dev Magic MCP requires an API key. This key is managed securely through the control-center secrets and is automatically injected into the MCP server's environment.
