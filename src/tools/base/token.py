from typing import Tuple

def extract_token_from_headers(headers: dict[str, str]) -> Tuple[str, str]:

    # Lista en orden de prioridad: (nombre_header, función para extraer token)
    token_sources = {
        "x_session_token": lambda h: h.get("x_session_token"),
        "authorization": lambda h: h.get("authorization")[7:] if h.get("authorization", "").lower().startswith("bearer ") else "",
        "meteor_token": lambda h: h.get("meteor_token"),
        "x-meteor-header": lambda h: h.get("x-meteor-header"),
    }

    for source, extractor in token_sources.items():
        token = extractor(headers)
        if token:
            return token, source

    return "", ""
