# Memoria simple por sesión
sessions = {}

def add_to_memory(session_id, role, text):
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append({"role": role, "text": text})

def get_memory(session_id):
    return "\n".join([f"{m['role']}: {m['text']}" for m in sessions.get(session_id, [])])
