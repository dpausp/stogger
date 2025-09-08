#!/usr/bin/env python3
"""🔥 Live Editing Demo - Interactive Code Transformation with Real-time Editing

This demo showcases the revolutionary live editing feature where users can
edit AI transformation suggestions in real-time and have all edits recorded
for machine learning improvements.
"""

from pathlib import Path
import tempfile

# Sample code with various transformation opportunities
SAMPLE_CODE_WITH_PRINTS = """
import os
import sys
import json

def process_user_data(user_id, email, preferences):
    print("Starting user data processing")
    print(f"Processing user: {user_id}")
    print(f"Email: {email}")
    
    # Validate input
    if not user_id:
        print("Error: Missing user ID")
        return None
    
    if "@" not in email:
        print("Error: Invalid email format")
        return None
    
    # Process preferences
    print("Processing user preferences")
    processed_prefs = {}
    
    for key, value in preferences.items():
        print(f"Processing preference: {key} = {value}")
        if isinstance(value, str):
            processed_prefs[key] = value.lower()
        else:
            processed_prefs[key] = value
    
    # Save to database
    print("Saving to database")
    try:
        # Simulate database save
        result = {
            "user_id": user_id,
            "email": email,
            "preferences": processed_prefs,
            "status": "processed"
        }
        print(f"Successfully processed user {user_id}")
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return None

def main():
    print("User Data Processor v1.0")
    print("=" * 30)
    
    # Sample data
    users = [
        {"id": "user123", "email": "john@example.com", "prefs": {"theme": "DARK", "notifications": True}},
        {"id": "user456", "email": "jane@example.com", "prefs": {"theme": "LIGHT", "notifications": False}},
        {"id": "", "email": "invalid", "prefs": {}},  # Invalid data for testing
    ]
    
    print(f"Processing {len(users)} users")
    
    results = []
    for user in users:
        print(f"\\nProcessing user: {user['id']}")
        result = process_user_data(user["id"], user["email"], user["prefs"])
        if result:
            results.append(result)
            print("✓ User processed successfully")
        else:
            print("✗ User processing failed")
    
    print(f"\\nProcessing complete. {len(results)} users processed successfully.")
    
    # Save results
    output_file = "processed_users.json"
    print(f"Saving results to {output_file}")
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print("Results saved successfully")
    except Exception as e:
        print(f"Error saving results: {e}")

if __name__ == "__main__":
    main()
"""


def create_demo_file() -> Path:
    """Create a temporary demo file with lots of print statements."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(SAMPLE_CODE_WITH_PRINTS)
        return Path(f.name)


def main():
    """Run the live editing demo."""
    demo_file = create_demo_file()

    print("🔥 Live Editing Demo - Interactive Code Transformation")
    print("=" * 60)
    print(f"Demo file created: {demo_file}")
    print()
    print("This file contains 15+ print() statements that can be transformed")
    print("to structured logging with LIVE EDITING capabilities!")
    print()
    print("🔥 NEW FEATURES:")
    print("• Edit AI suggestions in real-time")
    print("• All edits are recorded for machine learning")
    print("• Syntax validation and error handling")
    print("• Learning insights generated from your edits")
    print()
    print("To run the live editing transformation:")
    print(f"  nicestlog ast interactive {demo_file} --verbose")
    print()
    print("Or disable live editing if you prefer classic mode:")
    print(f"  nicestlog ast interactive {demo_file} --no-live-editing")
    print()
    print("For external editor support (vim, nano, etc.):")
    print(f"  nicestlog ast interactive {demo_file} --external-editor")
    print()
    print("🎯 INTERACTIVE FLOW WITH LIVE EDITING:")
    print()
    print("1. AI suggests transformation:")
    print('   ./demo.py:5                    print("Starting user data processing")')
    print(
        '   ->                             log.info("print-message", _replace_msg="Starting user data processing")',
    )
    print()
    print("2. You get enhanced options:")
    print("   Replace? [Y]es/[n]o/[a]ll/[p]review/🔥[e]dit/[s]kip file/[q]uit:")
    print()
    print("3. Choose [e]dit to modify the AI suggestion:")
    print("   🔥 Live Code Editor - Pattern: print_to_structlog")
    print("   [Original Code]")
    print('   print("Starting user data processing")')
    print()
    print("   [Current Transformation]")
    print('   log.info("print-message", _replace_msg="Starting user data processing")')
    print()
    print("   🔥 [e]dit/[a]ccept/[r]eject/reset:")
    print()
    print("4. Edit the transformation to your liking:")
    print(
        '   Code: log.info("user-data-processing-started", _replace_msg="🚀 Starting user data processing")',
    )
    print()
    print("5. Accept or reject your edited version")
    print()
    print("6. At the end, get learning insights:")
    print("   🧠 Learning Insights:")
    print("   • Acceptance rate: 85.7%")
    print("   • Avg edit duration: 12.3s")
    print("   • Avg edits per session: 2.1")
    print("   • Common patterns:")
    print("     - Users prefer descriptive event names")
    print("     - Users often add emojis to messages")
    print("     - Users prefer snake_case for event names")
    print()
    print("   💾 Edit data saved to: nicestlog_edit_sessions_1234567890.json")
    print()
    print("🧠 MACHINE LEARNING:")
    print("All your edits are recorded in JSON format for future AI improvements!")
    print("The system learns from your preferences to make better suggestions.")
    print()
    print(f"Demo file: {demo_file}")
    print("Remember to delete the demo file when done!")
    print()
    print("🔥 READY TO REVOLUTIONIZE YOUR CODE TRANSFORMATIONS? 🔥")


if __name__ == "__main__":
    main()
