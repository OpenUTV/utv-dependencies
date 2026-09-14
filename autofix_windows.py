import os
import sys
import time
import json
import subprocess
import argparse
import uuid


def run_cmd(cmd, capture=True, input_str=None):
    """Utility to run shell commands."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, input=input_str
    )
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        if capture:
            print(result.stderr)
    return result


def notify(message, ntfy_url):
    """Send notification via ntfy.sh."""
    print(f"Notification: {message}")
    if ntfy_url:
        cmd = f'curl -s -d "{message}" {ntfy_url}'
        run_cmd(cmd)


def get_latest_run(repo, workflow):
    """Get the status of the most recent workflow run."""
    cmd = f"gh run list --workflow='{workflow}' -R {repo} --limit 1 --json databaseId,status,conclusion"
    res = run_cmd(cmd)
    if res.returncode == 0:
        data = json.loads(res.stdout)
        if len(data) > 0:
            return data[0]
    return None


def get_run_logs(run_id, repo):
    """Retrieve failed logs for a specific run."""
    cmd = f"gh run view {run_id} --log-failed -R {repo}"
    res = run_cmd(cmd)
    return res.stdout if res.returncode == 0 else ""


def trigger_new_run(repo, workflow):
    """Trigger a new workflow run."""
    print(f"Triggering new build for {workflow} in {repo}...")
    run_cmd(f"gh workflow run {workflow} --ref main -R {repo}", capture=False)
    # Give GitHub a moment to register the run
    time.sleep(10)


def apply_fix_with_gemini(logs, session_id, args):
    """Use Gemini CLI to analyze logs and apply a fix."""
    print(f"Invoking Gemini CLI (Session: {session_id}) for analysis and fix...")

    # Ensure common homebrew paths are in PATH so gemini can find rg
    env = os.environ.copy()

    # Sanitize PATH: Put Homebrew at the absolute front, remove duplicates
    current_paths = env.get("PATH", "").split(":")
    new_paths = ["/opt/homebrew/bin", "/usr/local/bin"]
    for p in current_paths:
        if p not in new_paths and p.strip():
            new_paths.append(p)
    env["PATH"] = ":".join(new_paths)

    # Debug tools
    print(f"DEBUG: Final PATH for Gemini: {env['PATH'][:200]}...")
    tools_to_check = ["rg", "git", "curl", "gh"]
    found_tools = {}
    for tool in tools_to_check:
        import shutil

        path = shutil.which(tool, path=env["PATH"])
        found_tools[tool] = path
        print(f"DEBUG: tool '{tool}' path: {path or 'NOT FOUND'}")

    # We construct a prompt that asks Gemini to fix the issue directly in the workspace.
    prompt = f"""
The CI build ({args.workflow}) in repository {args.repo} failed. 
Analyze the following logs and apply a fix to the repository thinking from first principles and keeping in mind the projects goals and architecture.

TOOL CONTEXT:
- Your PATH is initialized. 
- 'rg' (ripgrep) is available at: {found_tools.get('rg')}
- 'git' is available at: {found_tools.get('git')}

FAILURE LOGS:
{logs[-10000:]}

INSTRUCTION: Fix the issue described in the logs using your tools. After fixing, commit and push your changes with a descriptive commit message. Use Conventional Commits.
"""

    # We try to resume first. If it fails, we use --session-id to create it.
    res_list = subprocess.run(
        ["gemini", "--list-sessions"], capture_output=True, text=True, env=env
    )
    has_session = session_id in res_list.stdout

    base_cmd = [
        "gemini",
        "-m",
        args.model,
        "--thinking",
        args.thinking,
        "--prompt",
        prompt,
        "--approval-mode",
        "yolo",
        "--skip-trust",
        "--raw-output",
        "--accept-raw-output-risk",
    ]

    if has_session:
        print(f"Resuming existing session {session_id}...")
        cmd = base_cmd + ["--resume", session_id]
    else:
        print(f"Creating new session {session_id}...")
        cmd = base_cmd + ["--session-id", session_id]

    # Stream the output so we can see what's happening
    process = subprocess.Popen(
        cmd, stdout=sys.stdout, stderr=sys.stderr, env=env, text=True
    )

    process.wait()
    return process.returncode == 0


def load_env(file_path=".env"):
    """Simple parser to load .env file into os.environ."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(
                        key.strip(), value.strip().strip('"').strip("'")
                    )


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Auto-fix CI failures using Gemini CLI."
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("AUTOFIX_REPO"),
        help="GitHub repository (e.g., owner/repo). Env: AUTOFIX_REPO",
    )
    parser.add_argument(
        "--workflow",
        default=os.environ.get("AUTOFIX_WORKFLOW"),
        help="Workflow filename (e.g., build.yml). Env: AUTOFIX_WORKFLOW",
    )
    parser.add_argument(
        "--ntfy-url",
        default=os.environ.get("AUTOFIX_NTFY_URL"),
        help="ntfy.sh URL for notifications. Env: AUTOFIX_NTFY_URL",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AUTOFIX_GEMINI_MODEL"),
        help="Gemini model to use. Env: AUTOFIX_GEMINI_MODEL",
    )
    parser.add_argument(
        "--thinking",
        default=os.environ.get("AUTOFIX_GEMINI_THINKING"),
        help="Gemini thinking mode. Env: AUTOFIX_GEMINI_THINKING",
    )
    args = parser.parse_args()

    # Validation: Ensure we have all required values from either CLI or ENV
    missing = []
    if not args.repo:
        missing.append("--repo (or AUTOFIX_REPO)")
    if not args.workflow:
        missing.append("--workflow (or AUTOFIX_WORKFLOW)")
    if not args.ntfy_url:
        missing.append("--ntfy-url (or AUTOFIX_NTFY_URL)")
    if not args.model:
        missing.append("--model (or AUTOFIX_GEMINI_MODEL)")
    if not args.thinking:
        missing.append("--thinking (or AUTOFIX_GEMINI_THINKING)")

    if missing:
        parser.print_help()
        print(f"\nError: Missing required configuration: {', '.join(missing)}")
        sys.exit(1)

    session_id = str(uuid.uuid4())

    # Ensure we are in a git repo
    if not os.path.exists(".git"):
        print("Error: Must be run from the root of a git repository.")
        sys.exit(1)

    # Self-caffeinate on macOS
    if sys.platform == "darwin":
        subprocess.Popen(
            ["caffeinate", "-d", "-i", "-m", "-s", "-u", "-w", str(os.getpid())]
        )

    notify(f"🤖 Dependency CI Agent started. Session: {session_id}", args.ntfy_url)

    # Check for existing active runs before triggering
    latest = get_latest_run(args.repo, args.workflow)
    if latest and latest.get("status") in ["in_progress", "queued"]:
        run_id = latest.get("databaseId")
        notify(
            f"🔎 Found active run {run_id} ({latest.get('status')}). Monitoring...",
            args.ntfy_url,
        )
    elif not latest or latest.get("status") == "completed":
        trigger_new_run(args.repo, args.workflow)

    while True:
        run = get_latest_run(args.repo, args.workflow)
        if not run:
            print("Waiting for run to appear...")
            time.sleep(30)
            continue

        run_id = run.get("databaseId")
        status = run.get("status")
        conclusion = run.get("conclusion")

        if status in ["in_progress", "queued"]:
            print(f"Run {run_id} is {status}. Waiting 60s...")
            time.sleep(60)
            continue

        if status == "completed":
            if conclusion == "success":
                notify(f"✅ Build {run_id} Succeeded!", args.ntfy_url)
                break
            elif conclusion == "failure":
                notify(f"❌ Build {run_id} Failed! Starting auto-fix...", args.ntfy_url)

                logs = get_run_logs(run_id, args.repo)
                if apply_fix_with_gemini(logs, session_id, args):
                    notify(
                        f"🚀 Gemini applied and pushed fix for {run_id}. Restarting build...",
                        args.ntfy_url,
                    )
                    trigger_new_run(args.repo, args.workflow)
                else:
                    notify(
                        "⚠️ Gemini was unable to apply a fix. Manual intervention required.",
                        args.ntfy_url,
                    )
                    break
            else:
                print(f"Run {run_id} completed with status: {conclusion}. Exiting.")
                break


if __name__ == "__main__":
    main()
