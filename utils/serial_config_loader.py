import json

def load_saved_serial_config(reader, on_status=None):
    try:
        with open("serial_settings.json", "r") as f:
            settings = json.load(f)

        reader.apply_parsing_settings(
            int(settings["start_ascii"]),
            int(settings["end_ascii"]),
            [p.strip() for p in settings["prefixes"].split(',') if p.strip()],
            int(settings["expected_length"]),
            settings["remove_zeros"],
            settings["reverse"],
            settings["digits_only"],
            enabled=settings["parsing_enabled"],
            use_index_mode=settings["use_index_mode"],
            start_index=int(settings["start_index"])
        )

        if on_status:
            on_status("✅ Applied saved parsing config.")
        return True

    except Exception as e:
        if on_status:
            on_status(f"⚠️ Could not apply saved config: {e}", error=True)
        return False
