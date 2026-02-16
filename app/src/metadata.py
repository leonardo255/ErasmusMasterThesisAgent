from datetime import datetime

def get_readable_timestamp():
    return datetime.now().isoformat()

def add_agent_metadata(document: dict, agent_name: str, agent_version: str, agent_model: str):
    """
    Adds or updates the 'agents' list in document metadata.
    """
    metadata    = document.get("metadata", {})
    source_id   = metadata.get("source", {}).get("doc_id", "unknown")
    agents      = metadata.get("agents", [])

    agents.append({
        "name": agent_name,
        "version": agent_version,
        "model": agent_model,
        "timestamp": get_readable_timestamp(),
    })

    metadata["agents"] = agents
    document["metadata"] = metadata
    return document


def add_evaluation_metadata(document: dict, reference_doc_id: str, evaluated_doc_id: str, model: str):
    """
    Adds evaluation-level metadata to document.
    """
    metadata = document.get("metadata", {})

    metadata["evaluation"] = {
        "model": model,
        "reference_doc_id": reference_doc_id,
        "evaluated_doc_id": evaluated_doc_id,
        "timestamp": get_readable_timestamp(),
    }

    document["metadata"] = metadata
    return document