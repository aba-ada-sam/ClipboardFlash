"""Small Windows helpers that do not depend on Qt (so they are unit-testable)."""


def ps_quote(value) -> str:
    """Quote a value as a PowerShell single-quoted string literal.

    Inside '...' the only special character is the quote itself, escaped by doubling.
    Without this a path such as C:\\Users\\O'Brien breaks (or injects into) the script.
    """
    return "'" + str(value).replace("'", "''") + "'"


def shortcut_script(lnk_path, target, arguments, working_dir) -> str:
    return (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut({ps_quote(lnk_path)}); "
        f"$s.TargetPath = {ps_quote(target)}; "
        f"$s.Arguments = {ps_quote(arguments)}; "
        f"$s.WorkingDirectory = {ps_quote(working_dir)}; "
        "$s.Description = 'Clipboard Flash'; "
        "$s.Save()"
    )
