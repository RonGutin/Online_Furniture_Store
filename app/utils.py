import re


def transform_pascal_to_snake(text):
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """
    text = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
    return text.upper()
