from __future__ import annotations

import os
import webbrowser


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(root, "csv_expr_viewer.html")
    url = f"file://{html_path}"
    print(f"Open: {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    main()
