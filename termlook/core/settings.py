"""Validated preferences independent of GTK."""
from dataclasses import asdict, dataclass
import re


@dataclass
class Settings:
    font: str = 'Monospace 11'
    foreground: str = '#d8d6eb'
    background: str = '#202127'
    scrollback: int = 20000
    cursor: str = 'block'
    blink: bool = False
    audible_bell: bool = False
    scroll_on_output: bool = False
    scroll_on_keystroke: bool = True
    padding: int = 12
    sidebar_width: int = 182
    shell: str = ''
    close_to_tray: bool = True

    @classmethod
    def from_data(cls, data):
        result = cls()
        if not isinstance(data, dict):
            return result
        for name, default in asdict(result).items():
            value = data.get(name, default)
            if type(value) is not type(default):
                continue
            if name in ('foreground', 'background') and not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
                continue
            if name == 'cursor' and value not in ('block', 'ibeam', 'underline'):
                continue
            if name == 'font' and (not value.strip() or len(value) > 200):
                continue
            bounds = {'scrollback': (100, 1000000), 'padding': (0, 40), 'sidebar_width': (140, 320)}
            if name in bounds:
                value = max(bounds[name][0], min(bounds[name][1], value))
            setattr(result, name, value)
        return result

    def to_data(self):
        return asdict(self)
