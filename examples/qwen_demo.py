"""
Qwen3 8B Coding Agent Demo

Demonstrates the capabilities of the integrated Qwen3 8B local coding agent.

Prerequisites:
- LM Studio or Ollama running with Qwen3 8B model
- Local server at http://localhost:1234/v1 (or update endpoint below)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.models.qwen import QwenModel
from core.logger import setup_logger

logger = setup_logger(__name__)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_code_generation():
    """Demonstrate code generation."""
    print_section("Demo 1: Code Generation")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    task = "Create a Python function that reads a CSV file and returns a list of dictionaries"
    print(f"Task: {task}\n")
    
    print("Generating code...")
    code = qwen.generate_code(
        task=task,
        language="python",
        context="Use the csv module and include error handling"
    )
    
    print("Generated Code:")
    print("-" * 80)
    print(code)
    print("-" * 80)


def demo_code_explanation():
    """Demonstrate code explanation."""
    print_section("Demo 2: Code Explanation")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    code_snippet = """
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:
        return 1
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
"""
    
    print("Code to Explain:")
    print("-" * 80)
    print(code_snippet)
    print("-" * 80)
    
    print("\nGenerating explanation...")
    explanation = qwen.explain_code(code_snippet, language="python")
    
    print("\nExplanation:")
    print("-" * 80)
    print(explanation)
    print("-" * 80)


def demo_debugging():
    """Demonstrate debugging assistance."""
    print_section("Demo 3: Debugging Assistance")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

result = calculate_average([])
"""
    
    error_message = "ZeroDivisionError: division by zero"
    
    print("Buggy Code:")
    print("-" * 80)
    print(buggy_code)
    print("-" * 80)
    
    print(f"\nError: {error_message}\n")
    
    print("Generating debugging solution...")
    solution = qwen.debug_code(
        code=buggy_code,
        error=error_message,
        language="python"
    )
    
    print("\nDebugging Solution:")
    print("-" * 80)
    print(solution)
    print("-" * 80)


def demo_refactoring():
    """Demonstrate code refactoring."""
    print_section("Demo 4: Code Refactoring")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    old_code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
"""
    
    print("Original Code:")
    print("-" * 80)
    print(old_code)
    print("-" * 80)
    
    goal = "Make it more Pythonic using list comprehension and add type hints"
    print(f"\nRefactoring Goal: {goal}\n")
    
    print("Generating refactored code...")
    improved = qwen.refactor_code(
        code=old_code,
        goal=goal,
        language="python"
    )
    
    print("\nRefactored Code:")
    print("-" * 80)
    print(improved)
    print("-" * 80)


def demo_code_completion():
    """Demonstrate code completion."""
    print_section("Demo 5: Code Completion")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    prefix = """
class UserManager:
    def __init__(self, database):
        self.db = database
    
    def create_user(self, username, email):
        # TODO: Implement user creation
"""
    
    print("Code Prefix:")
    print("-" * 80)
    print(prefix)
    print("-" * 80)
    
    print("\nGenerating completion...")
    completion = qwen.complete_code(
        prefix=prefix,
        language="python"
    )
    
    print("\nCompleted Code:")
    print("-" * 80)
    print(completion)
    print("-" * 80)


def demo_multi_language():
    """Demonstrate multi-language support."""
    print_section("Demo 6: Multi-Language Support")
    
    qwen = QwenModel(endpoint="http://localhost:1234/v1")
    
    languages = ["javascript", "typescript", "java"]
    task = "Create a function to validate email addresses"
    
    for lang in languages:
        print(f"\n{lang.upper()}:")
        print("-" * 80)
        
        code = qwen.generate_code(
            task=task,
            language=lang,
            context="Include regex pattern for validation"
        )
        
        print(code)
        print("-" * 80)


def check_connection():
    """Check if Qwen server is accessible."""
    print_section("Connection Check")
    
    try:
        qwen = QwenModel(endpoint="http://localhost:1234/v1")
        provider = qwen._get_provider()
        
        if provider and provider.is_connected():
            print("✓ Successfully connected to Qwen3 server")
            
            # Get available models
            models = provider.get_models()
            if models:
                print(f"\nAvailable models:")
                for model_id, model_info in models.items():
                    print(f"  - {model_id}")
            
            return True
        else:
            print("✗ Failed to connect to Qwen3 server")
            print("\nPlease ensure:")
            print("  1. LM Studio or Ollama is running")
            print("  2. Qwen3 8B model is loaded")
            print("  3. Server is accessible at http://localhost:1234/v1")
            return False
            
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("  QWEN3 8B CODING AGENT DEMONSTRATION")
    print("=" * 80)
    
    # Check connection first
    if not check_connection():
        print("\nExiting due to connection failure.")
        return
    
    # Run demos
    demos = [
        ("Code Generation", demo_code_generation),
        ("Code Explanation", demo_code_explanation),
        ("Debugging", demo_debugging),
        ("Refactoring", demo_refactoring),
        ("Code Completion", demo_code_completion),
        ("Multi-Language", demo_multi_language),
    ]
    
    print("\n\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Run All")
    print("  0. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (0-7): ").strip()
            
            if choice == "0":
                print("\nExiting demo.")
                break
            elif choice == str(len(demos) + 1):
                # Run all demos
                for name, demo_func in demos:
                    try:
                        demo_func()
                        input("\nPress Enter to continue to next demo...")
                    except Exception as e:
                        print(f"\n✗ Error in {name} demo: {e}")
                        logger.error(f"Demo error: {e}", exc_info=True)
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(demos):
                idx = int(choice) - 1
                name, demo_func = demos[idx]
                try:
                    demo_func()
                except Exception as e:
                    print(f"\n✗ Error: {e}")
                    logger.error(f"Demo error: {e}", exc_info=True)
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nExiting demo.")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            logger.error(f"Demo error: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("  Demo complete. Thank you!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
