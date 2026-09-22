"""DOM Element Inspector & Selector Discovery.

Extracts structured inventories of interactive elements (buttons, forms,
inputs, tables, headings) from HTML and provides live CSS selector querying.
"""

from typing import Any

from bs4 import BeautifulSoup


class ElementInspector:
    """Inspects DOM elements and executes CSS selector queries against HTML."""

    @staticmethod
    def _build_selector(tag_name: str, el: Any) -> str:
        """Construct a resilient CSS selector for an element."""
        elem_id = el.get("id")
        if (
            elem_id
            and isinstance(elem_id, str)
            and not elem_id.startswith(("ember", "react-", ":r"))
        ):
            return f"#{elem_id}"

        name = el.get("name")
        if name and isinstance(name, str):
            return f'{tag_name}[name="{name}"]'

        classes = el.get("class", [])
        if isinstance(classes, list) and classes:
            # Filter out dynamic or long utility classes
            clean_classes = [
                c for c in classes if len(c) < 35 and not c.startswith(("css-", "style-"))
            ]
            if clean_classes:
                return f"{tag_name}.{clean_classes[0]}"

        elem_type = el.get("type")
        if elem_type and isinstance(elem_type, str):
            return f'{tag_name}[type="{elem_type}"]'

        return tag_name

    @classmethod
    def inspect_html(cls, html: str) -> dict[str, Any]:
        """Extract a structured inventory of interactive and key content elements from HTML."""
        if not html:
            return {
                "summary": {
                    "total_elements": 0,
                    "buttons": 0,
                    "inputs": 0,
                    "tables": 0,
                    "headings": 0,
                },
                "buttons": [],
                "inputs": [],
                "tables": [],
                "headings": [],
            }

        soup = BeautifulSoup(html, "html.parser")

        # 1. Buttons & Clickable CTAs
        buttons: list[dict[str, Any]] = []
        button_tags = soup.find_all(
            lambda tag: (
                tag.name == "button"
                or (tag.name == "input" and tag.get("type") in ("button", "submit", "reset"))
                or (tag.get("role") == "button")
                or (
                    tag.name == "a"
                    and any("btn" in c or "button" in c for c in tag.get("class", []))
                )
            )
        )

        for btn in button_tags[:60]:  # Cap to first 60 buttons
            text = btn.get_text(strip=True)
            if not text and btn.get("value"):
                text = str(btn.get("value")).strip()
            if not text and btn.get("aria-label"):
                text = str(btn.get("aria-label")).strip()

            classes = btn.get("class", [])
            class_list = classes if isinstance(classes, list) else [str(classes)]
            elem_id = btn.get("id")

            buttons.append(
                {
                    "tag": btn.name,
                    "text": text[:80] if text else "(Icon/Empty)",
                    "id": str(elem_id) if elem_id else None,
                    "classes": class_list[:5],
                    "type": btn.get("type") or btn.get("role"),
                    "selector": cls._build_selector(btn.name, btn),
                    "disabled": btn.has_attr("disabled"),
                }
            )

        # 2. Form Inputs & Selects
        inputs: list[dict[str, Any]] = []
        input_tags = soup.find_all(["input", "select", "textarea"])

        for inp in input_tags[:60]:  # Cap to first 60 inputs
            inp_type = inp.get("type", "text") if inp.name == "input" else inp.name
            if inp_type in ("hidden", "button", "submit", "reset"):
                continue  # Skip buttons and hidden fields

            name = inp.get("name")
            elem_id = inp.get("id")
            placeholder = inp.get("placeholder")
            value = inp.get("value")

            inputs.append(
                {
                    "tag": inp.name,
                    "type": str(inp_type),
                    "name": str(name) if name else None,
                    "id": str(elem_id) if elem_id else None,
                    "placeholder": str(placeholder)[:80] if placeholder else None,
                    "value": str(value)[:80] if value else None,
                    "required": inp.has_attr("required"),
                    "selector": cls._build_selector(inp.name, inp),
                }
            )

        # 3. Tables & Data Grids
        tables: list[dict[str, Any]] = []
        table_tags = soup.find_all("table")

        for tbl in table_tags[:15]:  # Cap to 15 tables
            elem_id = tbl.get("id")
            headers = [th.get_text(strip=True) for th in tbl.find_all("th")[:10]]
            rows = tbl.find_all("tr")

            tables.append(
                {
                    "id": str(elem_id) if elem_id else None,
                    "selector": f"#{elem_id}" if elem_id else "table",
                    "headers": headers,
                    "rows_count": len(rows),
                }
            )

        # 4. Headings Outline
        headings: list[dict[str, Any]] = []
        for h in soup.find_all(["h1", "h2", "h3"])[:50]:
            h_text = h.get_text(strip=True)
            if h_text:
                elem_id = h.get("id")
                headings.append(
                    {
                        "level": h.name,
                        "text": h_text[:120],
                        "id": str(elem_id) if elem_id else None,
                        "selector": f"#{elem_id}" if elem_id else h.name,
                    }
                )

        return {
            "summary": {
                "total_elements": len(soup.find_all()),
                "buttons": len(buttons),
                "inputs": len(inputs),
                "tables": len(tables),
                "headings": len(headings),
            },
            "buttons": buttons,
            "inputs": inputs,
            "tables": tables,
            "headings": headings,
        }

    @classmethod
    def query_selector(cls, html: str, selector: str) -> list[dict[str, Any]]:
        """Query a custom CSS selector against the HTML and return matches with attributes."""
        if not html or not selector:
            return []

        soup = BeautifulSoup(html, "html.parser")
        try:
            matches = soup.select(selector)
        except Exception as exc:
            raise ValueError(f"Invalid CSS selector '{selector}': {exc}") from exc

        results: list[dict[str, Any]] = []
        for el in matches[:40]:  # Cap to 40 matches
            text = el.get_text(strip=True)
            classes = el.get("class", [])
            class_list = classes if isinstance(classes, list) else [str(classes)]

            # Extract useful attributes
            attrs: dict[str, str] = {}
            for k, v in el.attrs.items():
                if k in (
                    "href",
                    "src",
                    "value",
                    "placeholder",
                    "type",
                    "role",
                    "aria-label",
                    "title",
                    "name",
                    "id",
                ):
                    attrs[k] = str(v)
                elif k.startswith("data-"):
                    attrs[k] = str(v)

            results.append(
                {
                    "tag": el.name,
                    "id": el.get("id"),
                    "classes": class_list,
                    "text": text[:300] if text else "",
                    "attributes": attrs,
                    "html_preview": str(el)[:400],
                }
            )

        return results
