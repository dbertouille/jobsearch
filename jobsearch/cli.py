import argparse
import json
import logging
import sys

from jobsearch import discover


def cmd_discover(_args) -> None:
    jobs = discover.run()
    print(f"Discovered {len(jobs)} jobs. Run 'list' to see them.")


def cmd_list(args) -> None:
    state = discover.load_state()
    dismissed = set(state.get("dismissed", []))
    applied = set(state.get("applied", []))
    jobs = [
        j for j in state.get("jobs", [])
        if j["id"] not in dismissed
        and (args.applied == (j["id"] in applied))
        and (args.company is None or j["company"] == args.company)
    ][:args.count]

    if not jobs:
        print("[]")
        return

    print(json.dumps(jobs, indent=2))


def cmd_companies(args) -> None:
    state = discover.load_state()
    slugs_with_jobs = {j["company"] for j in state.get("jobs", [])}
    companies = [
        {"slug": slug, "source": data.get("source")}
        for slug, data in sorted(state.get("companies", {}).items())
        if not args.with_jobs or slug in slugs_with_jobs
    ]
    print(json.dumps(companies, indent=2))


def cmd_get(args) -> None:
    state = discover.load_state()
    jobs = state.get("jobs", [])
    job = next((j for j in jobs if j["id"] == args.job_id), None)

    if job is None:
        print(f"No job found with ID {args.job_id}.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(job, indent=2))


def cmd_status(_args) -> None:
    state = discover.load_state()
    print(json.dumps({"last_discover_time": state.get("last_discover_time")}, indent=2))


def cmd_apply(args) -> None:
    state = discover.load_state()
    applied = state.get("applied", [])

    if args.job_id in applied:
        print(f"Job {args.job_id} is already marked as applied.")
        return

    applied.append(args.job_id)
    state["applied"] = applied
    discover.save_state(state)
    print(f"Marked job {args.job_id} as applied.")


def cmd_dismiss(args) -> None:
    state = discover.load_state()
    dismissed = state.get("dismissed", [])

    if args.job_id in dismissed:
        print(f"Job {args.job_id} is already dismissed.")
        return

    dismissed.append(args.job_id)
    state["dismissed"] = dismissed
    discover.save_state(state)
    print(f"Dismissed job {args.job_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="jobsearch", description="Job search CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="Discover and filter remote jobs")

    subparsers.add_parser("status", help="Show job search status")

    list_parser = subparsers.add_parser("list", help="List previously discovered jobs")
    list_parser.add_argument(
        "--count", type=int, default=10, metavar="N",
        help="Number of jobs to show (default: 10)",
    )
    list_parser.add_argument(
        "--applied", action="store_true",
        help="Show only jobs marked as applied",
    )
    list_parser.add_argument(
        "--company", metavar="SLUG",
        help="Only show jobs from this company slug",
    )

    companies_parser = subparsers.add_parser("companies", help="List all known companies")
    companies_parser.add_argument(
        "--with-jobs", action="store_true",
        help="Only show companies with active job postings",
    )

    get_parser = subparsers.add_parser("get", help="Print full JSON for a job by ID")
    get_parser.add_argument("job_id", help="ID of the job to retrieve")

    apply_parser = subparsers.add_parser("apply", help="Mark a job as applied by ID")
    apply_parser.add_argument("job_id", help="ID of the job to mark as applied")

    dismiss_parser = subparsers.add_parser("dismiss", help="Dismiss a job by ID")
    dismiss_parser.add_argument("job_id", help="ID of the job to dismiss")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        stream=sys.stderr,
        format="%(levelname)s: %(message)s",
    )

    if args.command == "discover":
        cmd_discover(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "companies":
        cmd_companies(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "apply":
        cmd_apply(args)
    elif args.command == "dismiss":
        cmd_dismiss(args)
