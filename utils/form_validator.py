def validate_request_data(data: dict, required_fields: dict):
    missed_input_error = "Missing field(s)="
    invalid_input_error = "Invalid field(s)="
    for field, field_type in required_fields.items():
        if field not in data or (data[field] == "" or data[field] is None):
            missed_input_error += f"{field.upper()}-"

        elif not isinstance(data[field], field_type):
            invalid_input_error += f"{field.upper()}:{field_type.__name__}-"

    err = ""
    if missed_input_error != "Missing field(s)=":
        err += missed_input_error[:-1] + "."
    if invalid_input_error != "Invalid field(s)=":
        err += invalid_input_error[:-1]
    if err:
        return False, err

    return True, None
