import discord
import config
import typing
import time
import subprocess
import sys


def is_staff(member: discord.Member) -> bool:
    """Check if a Discord member has a staff role."""
    staff_roles_set = set(config.config["STAFF_ROLES"])
    return any(role.id in staff_roles_set for role in member.roles)


def wait(seconds: int = 5):
    """Wait for a number of seconds before continuing."""
    time.sleep(seconds)


def check_for_ffmpeg():
    """Check if ffmpeg is installed on the system."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("ffmpeg is not installed. Please install it to use this feature.")
        sys.exit(1)
