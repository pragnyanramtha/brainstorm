"""
Integration test for the backend core logic.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import init_db, close_db, async_session_factory, User, Project, Message
from backend.core.intake import analyze_intent
from backend.core.clarifier import generate_clarifications
from backend.core.optimizer import build_optimized_prompt
from backend.memory.user_profile import ensure_user_exists
from backend.skills.seed_skills import seed_skills
from backend.mcps.seed_mcps import seed_mcps

async def main():
    print("🚀 Starting integration test...")
    
    # Init DB
    await init_db()
    
    async with async_session_factory() as session:
        # Seed
        await seed_skills(session)
        await seed_mcps(session)
        
        # Ensure user
        user = await ensure_user_exists(session)
        user_profile = user.to_dict()
        print(f"✓ User profile loaded: {user_profile['technical_level']}")

        # Test Case 1: Simple ambiguous request
        message = "build me a website"
        print(f"\n--- Testing Intake: '{message}' ---")
        
        intake = await analyze_intent(
            user_message=message,
            user_profile=user_profile,
        )
        print(f"Intake Result: type={intake.task_type}, conf={intake.confidence_score}%")
        print(f"Intent: {intake.interpreted_intent}")
        
        if intake.confidence_score < 85:
            print("\n--- Testing Clarifier ---")
            clarification = await generate_clarifications(
                intake_analysis=intake.model_dump(),
                user_message=message,
                user_profile=user_profile,
            )
            if clarification.needs_clarification:
                print("Questions generated:")
                for q in clarification.questions:
                    print(f"- {q.question} ({q.question_type})")
            else:
                print("No clarification needed (startling for this query)")

        # Test Case 2: Clear technical request
        message_tech = "Write a Python script to parse a CSV file and plot a histogram of the 'age' column using matplotlib."
        print(f"\n--- Testing Optimizer: '{message_tech}' ---")
        
        intake_tech = await analyze_intent(
            user_message=message_tech,
            user_profile=user_profile,
        )
        print(f"Intake Result: type={intake_tech.task_type}, conf={intake_tech.confidence_score}%")

        prompt = await build_optimized_prompt(
            user_message=message_tech,
            intake_analysis=intake_tech.model_dump(),
            user_profile=user_profile,
            selected_skills=["clean_code", "python_expert"], # Simulate selection
        )
        
        print("\n--- Optimized Prompt (first 500 chars) ---")
        print(prompt[:500] + "...")
        print("------------------------------------------")

    await close_db()
    print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(main())
