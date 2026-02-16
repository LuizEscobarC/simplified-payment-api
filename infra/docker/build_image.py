#!/usr/bin/env python3
"""Build image helper (Python wrapper).

Usage: python3 build_image.py [tag]
"""
import subprocess
import sys
from datetime import datetime


def run(cmd, **kwargs):
    print("$ ", " ".join(cmd))
    return subprocess.run(cmd, check=False, text=True, **kwargs)


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "simplified-payment:local"
    build_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        vcs_ref = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        vcs_ref = "unknown"
    try:
        version = subprocess.check_output(["git", "describe", "--tags", "--always"], text=True).strip()
    except Exception:
        version = "dev"

    cmd = [
        "docker", "build", "--progress=plain",
        "--build-arg", "NODE_ENV=development",
        "--build-arg", f"BUILD_DATE={build_date}",
        "--build-arg", f"VCS_REF={vcs_ref}",
        "--build-arg", f"VERSION={version}",
        "-f", "infra/docker/php/Dockerfile.local",
        "-t", tag,
        ".",
    ]

    r = run(cmd)
    if r.returncode != 0:
        print("Build failed", file=sys.stderr)
        sys.exit(r.returncode)

    print("\n== Image -> {} ==".format(tag))
    run(["docker", "image", "ls", "--format", "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}", tag])

    print("\n== History (layers) -> {} ==".format(tag))
    run(["docker", "history", "--no-trunc", tag])


if __name__ == "__main__":
    main()
