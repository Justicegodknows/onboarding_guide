import re

# Strip CoT reasoning blocks before the answer is delivered to the user.
# \s* after the closing tag absorbs the trailing newline the model typically emits.
_SCRATCHPAD_RE = re.compile(r"<scratchpad>.*?</scratchpad>\s*", re.DOTALL | re.IGNORECASE)
_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def strip_scratchpad(text: str) -> str:
    text = _SCRATCHPAD_RE.sub("", text)
    text = _THINK_RE.sub("", text)
    return text.strip()
