"""
Runs the full Ascent Analytics data pipeline end to end, in the correct
order, stopping immediately and clearly if any step fails rather than
continuing on bad data.

Usage:
    python run_pipeline.py            # generation -> cleaning -> warehouse
    python run_pipeline.py --test     # same, then runs the full test suite

Works identically on Windows, macOS, and Linux — no extra tools beyond
Python itself and the packages in requirements.txt. See Makefile for a
Unix-style equivalent (same steps, different entry point).
"""

import subprocess
import sys
import time

STEPS = [
    ("Generating reference data (regions, guides, routes)", "src.generation.generate_reference_data"),
    ("Generating transactions (tours, bookings, payments)", "src.generation.generate_transactions"),
    ("Generating extensions (reviews, weather, marketing, website, equipment)", "src.generation.generate_extensions"),
    ("Cleaning core tables", "src.cleaning.run_pipeline"),
    ("Cleaning extension tables", "src.cleaning.run_pipeline_extensions"),
    ("Building the SQL warehouse", "src.warehouse.build_warehouse"),
    ("Applying SQL views", "src.warehouse.apply_views"),
    ("Exporting for Power BI", "src.warehouse.export_for_powerbi"),
]


def run_step(step_number: int, total_steps: int, description: str, module: str) -> float:
    print(f"\n[{step_number}/{total_steps}] {description}")
    print(f"      python -m {module}")
    start = time.time()
    result = subprocess.run([sys.executable, "-m", module])
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n\u2717 Step {step_number} failed (exit code {result.returncode}) — stopping here.")
        print("  Fix the error above before re-running; later steps depend on this one's output.")
        sys.exit(result.returncode)

    print(f"      done in {elapsed:.1f}s")
    return elapsed


def main():
    run_tests = "--test" in sys.argv

    print("Ascent Analytics — full pipeline run")
    print("=" * 60)

    total_start = time.time()
    for i, (description, module) in enumerate(STEPS, start=1):
        run_step(i, len(STEPS), description, module)

    pipeline_elapsed = time.time() - total_start
    print("\n" + "=" * 60)
    print(f"Pipeline complete in {pipeline_elapsed:.1f}s — all 8 steps succeeded.")

    if run_tests:
        print("\nRunning the full test suite...")
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
        if result.returncode != 0:
            print("\n\u2717 Tests failed — pipeline output exists, but something's wrong with it.")
            sys.exit(result.returncode)
        print("\n\u2713 All tests passed against fresh pipeline output.")
    else:
        print("Run with --test to also run the full test suite against this output.")


if __name__ == "__main__":
    main()