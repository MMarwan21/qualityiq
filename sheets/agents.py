# handles all agent related operations
# Role detection logic

from .client import get_sheet
import os

def get_all_agents() -> list[dict]:
    """
    Read all rows from the agents sheet and return as 
    a list of dictionaries

    Returns a list of dicts with keys: name, email, role, active, color
    """
    sheet = get_sheet("Agents")
    rows  = sheet.get_all_values()
    # First row is the header — skip it
    if len(rows) <2:
        return []
    agents = []
    for row in rows[1:]:
        #skip empty rows
        if not row[0]:
            continue

        agents.append({
            "name": row[0].strip(),
            "email": row[1].strip().lower() if len(row) > 1 else "",
            "role": row[2].strip().lower() if len(row)> 2 else "agent",
            "active": str(row[3]).upper() == "TRUE" if len(row) > 3 else False,
            "color": row[4] if len(row) > 4 else "#0D9488",
        })

    return agents

def get_role(email: str) -> str:
    """
    Determine the role of a user based on their email.

    This is the core authorization function.
    Every protected route calls this to decide
    what the user is allowed to see and do.

    Args:
        email: the verified Google email address

    Returns:
        str: one of 'admin', 'management', 'agent', 'unauthorized'
    """
    if not email:
        return "unauthorized"
    email = email.lower().strip()

    # Check admin list first — hardcoded as env var
    # so it never accidentally ends up in the sheet
    admin_email = os.getenv("ADMIN_EMAIL", "").lower().strip()
    if email == admin_email:
        return "admin"
    
    # check agent sheet for everyone else
    for agent in get_all_agents():
        if agent["email"] == email:
            # found the email now check if it is active
            if not agent["active"]:
                return "unauthorized"
            role = agent["role"]
            if role == "management":
                return "management"
            if role == "admin":
                return "admin"
            return "agent"
    return "unauthroized"

def get_display_name(email: str) -> str:
    """
    Return the full name for a given email.
    Used to personalise the UI — "Welcome, Hossam"

    Args:
        email: Google email address

    Returns:
        str: full name from Agents sheet, or the part
             before @ if not found
    """
    email = email.lower().strip()

    for agent in get_all_agents():
        if agent["email"] == email:
            return agent["name"]

    # Fallback — use the part before @ as display name
    return email.split("@")[0]


def get_agent_by_email(email: str) -> dict | None:
    """
    Return the full agent record for a given email.

    Args:
        email: Google email address

    Returns:
        dict with agent data, or None if not found
    """
    email = email.lower().strip()

    for agent in get_all_agents():
        if agent["email"] == email:
            return agent

    return None


def get_agents_only() -> list[dict]:
    """
    Return only active agents — excludes management.
    Used to populate the agent dropdown in the
    evaluation form.

    Returns:
        list of agent dicts where role == 'agent'
        and active == True
    """
    return [
        a for a in get_all_agents()
        if a["role"] == "agent" and a["active"]
    ]


def save_agent(agent: dict) -> bool:
    """
    Add a new agent or update an existing one.
    Matches by name — if name exists, updates that row.
    If name doesn't exist, appends a new row.

    Args:
        agent: dict with keys name, email, role, active, color

    Returns:
        bool: True if successful
    """
    sheet = get_sheet("Agents")
    rows  = sheet.get_all_values()

    # Search for existing row by name
    for i, row in enumerate(rows[1:], start=2):
        if row[0].strip() == agent["name"].strip():
            # Update existing row
            sheet.update(
                f"A{i}:E{i}",
                [[
                    agent["name"],
                    agent["email"],
                    agent.get("role", "agent"),
                    "TRUE" if agent.get("active", True) else "FALSE",
                    agent.get("color", "#0D9488")
                ]]
            )
            return True

    # Not found — append new row
    sheet.append_row([
        agent["name"],
        agent["email"],
        agent.get("role", "agent"),
        "TRUE",
        agent.get("color", "#0D9488")
    ])
    return True


