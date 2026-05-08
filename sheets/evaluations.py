# sheets/evaluations.py
# All evaluation data operations
# Reads and writes to the Raw_Data Sheet
# Uses column-agnostic reading - finds columns by name
# not by position number

from .client import get_sheet
from .scoring import calculate_score, kpi_percent, kpi_tier
from datetime import datetime
import pytz

TIMEZONE = pytz.timezone("Africa/Cairo")


def _get_col(headers: list, name: str) -> int | None:
    """
    Find a column index by its header name.
    Returns None if the column doesn't exist.

    This is safer than hardcoding column numbers.
    """
    try:
        return headers.index(name)
    except ValueError:
        return None
    
def _safe_get(row: list, index: int | None) -> str:
    """
    Safely get a value from a row by index.
    Returns empty string if index is None or out of Range

    Prevents IndexError when rows have different lengths
    """
    if index is None or index >= len(row):
        return ""
    return str(row[index])

def get_all_evals(
        month_filter: str = "",
        agent_filter: str = "",
        published_only: bool = False
        ) -> list[dict]:
    """
    Read all evaluations from Raw_Data sheet.

    Args:
        month_filter: if set, only return evals for this month.
        agent_filter: if set, only return evals for this agent
        published_only: if True, only returns published evals

    Returns:
        list of evaluation dicts, each containing all fields
    """
    sheet   = get_sheet("Raw_Data")
    rows    = sheet.get_all_values()
    
    # Check if the sheet already has data or empty before we start the loop
    if len(rows)< 2:
        return []
    
    headers = rows[0]
    # Find all column positions by name
    # This is robus - works even if columns move

    mC  = _get_col(headers, "Month")
    pC  = _get_col(headers, "Published")
    dC  = _get_col(headers, "Dispute_Comment")
    dsC = _get_col(headers, "Dispute_Status")
    rC  = _get_col(headers, "Dispute_Reply")
    scC = _get_col(headers, "Score")

    evals = []

    for i, row in enumerate(rows[1:], start=2):
        # Skip empty rows
        if not row[0] or not row [1]:
            continue

        # Agent name is stored in column 26 
        # with column 2 as fallback for older rows
        agent_name = _safe_get(row, 26) or _safe_get(row, 2)
        month      = _safe_get(row, mC)

        # Apply filters
        if month_filter and month != month_filter:
            continue
        if agent_filter and agent_name != agent_filter:
            continue

        # Parse published flag
        pub_val     = _safe_get(row, pC).upper()
        published   = pub_val == "TRUE"

        if published_only and not published:
            continue

        # Parse score

        try:
            score = float(_safe_get(row, scC))
        except (ValueError, TypeError):
            score = 0.0
        
        evals.append({
            "rowIndex":             i,
            "timestamp":            _safe_get(row, 0),
            "bookingID":            _safe_get(row, 1),
            "agentName":            agent_name,
            "caseType":             _safe_get(row, 27) or _safe_get(row, 5),
            "creationDate":         _safe_get(row, 3),
            "resolvedDate":         _safe_get(row, 4),
            "month":                month,
            "published":            published,
            "score":                round(score, 1),
            "kpiTier":              kpi_tier(score),
            "kpiPercent":           kpi_percent(score),
            # Criteria ratings
            "ownership":            _safe_get(row, 6),
            "handover":             _safe_get(row, 8),
            "copyPaste":            _safe_get(row, 10),
            "correctEmail":         _safe_get(row, 11),
            "flow":                 _safe_get(row, 13),
            "clientApproach":       _safe_get(row, 15),
            "supplierApproach":     _safe_get(row, 17),
            "freshdesk":            _safe_get(row, 19),
            "juniper":              _safe_get(row, 21),
            # Criterion comments
            "ownershipComment":     _safe_get(row, 7),
            "handoverComment":      _safe_get(row, 9),
            "correctEmailComment":  _safe_get(row, 12),
            "flowComment":          _safe_get(row, 14),
            "clientApprachComment": _safe_get(row, 16),
            "supplierApproachComment": _safe_get(row, 18),
            "freshdeskComment":     _safe_get(row, 20),
            "juniperComment":       _safe_get(row, 22),
            "overallComment":       _safe_get(row, 23),
            "evaluatorEmail":       _safe_get(row, 25),
            # Dispute fields
            "disputeComment":       _safe_get(row, dC),
            "disputeStatus":        _safe_get(row, dsC),
            "disputeReply":         _safe_get(row, rC),
        })

    return evals


def get_available_months() -> list[str]:
    """
    Return sorted list of unique months that have evaluations.
    Used to populate the month filter dropdown.

    Returns:
        list of month strings e.g. [" January 2025", "February 2025"]
    """
    sheet = get_sheet("Raw_Data")
    # get_all_values is a function of gspread and returns a list of lists for all data in the sheet
    # we can use get_all_records and it returns a list of dicts but values are faster
    rows = sheet.get_all_values()

    if len(rows) < 2:
        return []

    headers = rows[0]
    mC = _get_col(headers, "Month")

    if mC is None:
        return []

    months = sorted(set(
        str(row[mC]).strip()
        for row in rows[1:]
        if len(row) > mC and str(row[mC]).strip()
    ))

    return months
    

def submit_evaluation(data: dict, evaluator_email: str) -> dict:
    """
    Write a new evaluation row to Raw_Data sheet.
    Calculates the score and stores it in the Score column.

    Args:
        data: evaluation data from the form
        evaluator_email: email of the user submitting
    
    Returns:
        dict with success flag and calculated score
    """

    sheet   = get_sheet("Raw_Data")
    headers = sheet.row_values(1)

    # Calculate score
    score = calculate_score(
        data,
        auto_fail = data.get("autoFail", False
        ))
    
    # Find column positions
    mC      =  _get_col(headers, "Month")
    pC     =  _get_col(headers, "Published")
    dC    =  _get_col(headers, "Dispute_Comment")
    dsC   =  _get_col(headers, "Dispute_Status")
    scC   =  _get_col(headers, "Score")
    # Build the row - 28 columns minimum to match the form fields
    max_col = max(filter(None, [mC, pC, dC, DsC, scC, 27])) + 1
    row = [""] * max_col

    # Timestamp in Cairo timezone
    now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

    row[0] = now
    row[1] = data.get("bookingID", "")
    row[2] = data.get("agentName", "")
    row[3] = data.get("creationDate", "")
    row[4] = data.get("resolvedDate", "")
    row[5] = data.get("caseType", "")
    row[6] = data.get("ownership", "")
    row[7] = data.get("ownershipComment", "")
    row[8] = data.get("handover", "")
    row[9] = data.get("handoverComment", "")
    row[10] = data.get("copyPaste", "")
    row[11] = data.get("correctEmail", "")
    row[12] = data.get("correctEmailComment", "")
    row[13] = data.get("flow", "")
    row[14] = data.get("flowComment", "")
    row[15] = data.get("clientApproach", "")
    row[16] = data.get("clientApprachComment", "")
    row[17] = data.get("supplierApproach", "")
    row[18] = data.get("supplierApproachComment", "")
    row[19] = data.get("freshdesk", "")
    row[20] = data.get("freshdeskComment", "")
    row[21] = data.get("juniper", "")
    row[22] = data.get("juniperComment", "")
    row[23] = data.get("overallComment", "")
    row[25] = evaluator_email
    row[26] = data.get("agentName", "")
    row[27] = data.get("caseType", "")
    if mC is not None:
        row[mC] = data.get("month", "")
    if pC is not None:
        row[pC] = "FALSE"
    if dC is not None:
        row[dC] = ""
    if dsC is not None:
        row[dsC] = ""
    if scC is not None:
        row[scC] = score

    sheet.append_row(row)

    return{"success": True, "score": score}


def toggle_publish(row_index: int, publish: bool) -> dict:
    """
    Publish or unpublish an evaluation by setting the Published column.

    Args:
        row_index: the row number of the evaluation to update
        publish: True to publish, False to unpublish
    Returns:
        dict with success flag
    """
    sheet = get_sheet("Raw_Data")
    headers = sheet.row_values(1)
    pC = _get_col(headers, "Published")

    if pC is None:
        return {"success": False, "error": "Published column not found - run setupSheets()"}
    
    # gspread uses 1-based column indexing
    sheet.update_cell(row_index, pC + 1, "TRUE" if publish else "FALSE")
    return {"success": True}

def submit_dispute(row_index: int, comment: str) -> dict:
    """
    Write an agent's dispute comment and set status to Pending

    Args:
        row_index: sheet row number of the evaluation to update
        comment: the agent's dispute comment text

    Returns:
        dict with success flag
    """
    sheet = get_sheet("Raw_Data")
    headers = sheet.row_values(1)
    dC = _get_col(headers, "Dispute_Comment")
    dsC = _get_col(headers, "Dispute_Status")

    if dC is not None:
        sheet.update_cell(row_index, dC + 1, comment)
    if dsC is not None:
        sheet.update_cell(row_index, dsC + 1, "Pending")
    return {"success": True}

def reply_dispute(row_index: int, reply: str) -> dict:
    """
    Write a manager's reply to a dispute

    Args:
        row_index: sheet row number of the evaluation to update
        reply: the manager's reply text

    Returns:
        dict with success flag
    """
    sheet = get_sheet("Raw_Data")
    headers = sheet.row_values(1)
    rC = _get_col(headers, "Dispute_Reply")

    if rC is None:
        return {
            "success" : False,
            "error": "Dispute_Reply column not found"
        }
    sheet.update_cell(row_index, rc + 1, reply)
    return {"success": True}

def resolve_dispute(row_index: int) -> dict:
    """
    Mark A dispute as resolved.
    Blocked if no reply has been written yet.

    Args:
        row_index: sheet row number of the evaluation to update
    Returns:
        dict with success flag and error message if blocked
    """

    sheet    = get_sheet("Raw_Data")
    headers  = sheet.row_values(1)
    dsC     = _get_col(headers, "Dispute_Status")
    rC     = _get_col(headers, "Dispute_Reply")

    # Block resolve if no reply exists

    if rC is not None:
        reply = sheet.cell(row_index, rC + 1).value or ""
        if not reply.strip():
            return {
                "success": False,
                "error": "Cannot resolve dispute without a manager reply"
            }
        
    if dsC is not None:
        sheet.update_cell(row_index, dsC + 1, "Resolved")

    return {"success": True}

def get_settings() -> dict:
    """
    Read the settings sheet and return as a dict.

    Returns:
        dict e.g {"evals_target": "20", "current_month" : "May 2026"}
    """
    sheet   = get_sheet("Settings")
    rows    = sheet.get_all_values()
    return {
        row[0]: row[1]
        for row in rows[1:]
        if row[0]
    }

def save_setting(key: str, value) -> bool:
    """
    Update a value in the Settings sheet
    Only the admin should call this 

    Args:
    key: the setting name e.g. "evals_target"
    value: the new value.

    Returns:
    bool: True if successful
    """

    sheet = get_sheet("Settings")
    rows  = sheet.get_all_values()

    for i, row in enumerate(rows[1:], start=2):
        if row[0] == key:
            sheet.update_cell(i, 2, value)
            return True
    # If key not found, append a new row
    sheet.append_row([key, value])
    return True
