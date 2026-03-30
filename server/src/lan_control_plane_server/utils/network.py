def normalize_mac_address(mac_address: str | None) -> str | None:
    if mac_address is None:
        return None

    normalized = mac_address.strip().lower().replace("-", ":")
    parts = normalized.split(":")

    if len(parts) != 6:
        raise ValueError(f"Invalid MAC address: {mac_address}")

    if any(len(part) != 2 for part in parts):
        raise ValueError(f"Invalid MAC address: {mac_address}")

    try:
        bytes.fromhex("".join(parts))
    except ValueError as exc:
        raise ValueError(f"Invalid MAC address: {mac_address}") from exc

    parts = [part.upper() for part in parts]

    return ":".join(parts)
