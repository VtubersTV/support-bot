import discord
import config
import typing
import time


def is_staff(member: discord.Member) -> bool:
    """Check if a Discord member has a staff role."""
    staff_roles = config.config["STAFF_ROLES"]
    # Create a set for fast membership testing
    staff_roles_set = set(staff_roles)
    # Check if any role id is in the staff roles
    return any(role.id in staff_roles_set for role in member.roles)


def wait(seconds: typing.Optional[int] = 5):
    """Wait for a number of seconds before continuing."""
    time.sleep(seconds if seconds is not None else 5)
