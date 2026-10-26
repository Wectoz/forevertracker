"""Cut the per-class sections out of Blizzard's forum patch notes, keeping only safe HTML."""

import html
from urllib.parse import urljoin
from dataclasses import dataclass, field
from html.parser import HTMLParser

from wowforever.forum import FORUM_URL

CLASSES = ("Druid", "Hunter", "Mage", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior")
CLASS_COLORS = {
    "Druid": "#FF7C0A", "Hunter": "#AAD372", "Mage": "#3FC7EB", "Paladin": "#F48CBA", "Priest": "#FFFFFF",
    "Rogue": "#FFF468", "Shaman": "#0070DD", "Warlock": "#8788EE", "Warrior": "#C69B6D",
}
_BY_KEY = {name.casefold(): name for name in CLASSES}

_ALLOWED = {"ul", "ol", "li", "strong", "b", "em", "i", "p", "br", "a"}
_DROPPED = {"script", "style"}  # removed together with their content
_QUOTES = {"aside", "blockquote"}
_BLOCK_HEADINGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6"}
_VOID = {"br", "img", "hr", "input", "meta", "link", "wbr", "source"}


def slug(name: str) -> str:
    return name.lower()


def class_for_slug(value: str) -> str | None:
    return _BY_KEY.get(value.casefold())


@dataclass(eq=False)  # nodes are compared by identity: two identical headings are still two headings
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list["_Node | str"] = field(default_factory=list)

    def elements(self) -> list["_Node"]:
        return [c for c in self.children if isinstance(c, _Node)]

    def text(self) -> str:
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {})
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, {k: v or "" for k, v in attrs})
        self._stack[-1].children.append(node)
        if tag not in _VOID:
            self._stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return

    def handle_data(self, data):
        self._stack[-1].children.append(data)


def _heading(li: _Node) -> str | None:
    """The text of the <strong> an <li> starts with, e.g. "Mage" in <li><strong>Mage</strong><ul>…"""
    first = next((c for c in li.children if not (isinstance(c, str) and not c.strip())), None)
    if isinstance(first, _Node) and first.tag == "strong":
        return first.text().strip().casefold()
    return None


def _walk(node: _Node):
    for child in node.elements():
        if child.tag in _QUOTES:
            continue  # a reply quoting the notes is not a new set of notes
        yield child, node
        yield from _walk(child)


def _classes_list(root: _Node) -> _Node | None:
    """The <ul> holding the class headings. Blizzard writes the "Classes" heading two ways:
    <li><strong>Classes</strong><ul>…</ul></li>, or <p><strong>Classes</strong></p> followed by <ul>…</ul>."""
    for node, parent in _walk(root):
        if node.tag == "li" and _heading(node) == "classes":
            found = next((c for c in node.elements() if c.tag == "ul"), None)
        elif node.tag in _BLOCK_HEADINGS and node.text().strip().casefold() == "classes":
            siblings = parent.elements()
            following = siblings[siblings.index(node) + 1:]
            found = following[0] if following and following[0].tag == "ul" else None
        else:
            continue
        if found is not None:
            return found
    return None


def _render(node: _Node | str) -> str:
    if isinstance(node, str):
        return html.escape(node, quote=False)
    if node.tag in _DROPPED:
        return ""
    inner = "".join(_render(c) for c in node.children)
    if node.tag not in _ALLOWED:
        return inner
    if node.tag == "br":
        return "<br>"
    if node.tag == "a":
        href = node.attrs.get("href", "").strip()
        if href.startswith("/") and not href.startswith("//"):
            href = urljoin(FORUM_URL, href)  # root-relative forum link
        if not href.startswith(("http://", "https://")):
            return inner  # in-page anchors and anything else stay plain text
        return f'<a href="{html.escape(href)}" target="_blank" rel="noopener nofollow">{inner}</a>'
    return f"<{node.tag}>{inner}</{node.tag}>"


def split_classes(cooked: str) -> dict[str, str]:
    builder = _TreeBuilder()
    builder.feed(cooked or "")
    builder.close()
    classes = _classes_list(builder.root)
    if classes is None:
        return {}
    sections = {}
    for class_li in (c for c in classes.elements() if c.tag == "li"):
        name = _BY_KEY.get(_heading(class_li) or "")
        body = next((c for c in class_li.elements() if c.tag == "ul"), None)
        if name and body is not None:
            sections[name] = _render(body)
    return sections
