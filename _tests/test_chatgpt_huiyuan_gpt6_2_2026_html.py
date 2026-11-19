"""Render chatgpt-huiyuan-gpt6-2-2026.md and check the HTML that Pages would show.

GitHub Pages runs kramdown on the Markdown body. This file uses Python-Markdown
for the same constructs in this article: links, tight ordered lists, tight
unordered lists, and tables. The assertions are on that generated HTML, not on
a hand-counted source dump.

Run: python3 _tests/test_chatgpt_huiyuan_gpt6_2_2026_html.py
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import markdown


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "chatgpt-huiyuan-gpt6-2-2026.md"

EXPECTED_TITLE = "chatgpt会员能用GPT-6.2吗？Work和Codex对照｜GPT20X"
EXPECTED_DESCRIPTION = (
    "chatgpt会员能用GPT-6.2吗？官方已向 Plus、Pro 等套餐在「工作」和 Codex 中逐步开放 "
    "GPT-6.2 Astra 和 Sol，不会加入普通聊天；本文按公告和帮助中心整理套餐对照、极速规则和找不到模型时怎么办，GPT20X 整理。"
)

MAIN_SITE_LINKS = (
    ("https://gpt20x.com/", "ChatGPT充值"),
    ("https://gpt20x.com/", "GPT20X"),
)

OFFICIAL_SOURCES = (
    "https://openai.com/index/introducing-gpt-6-2-astra-sol/",
    "https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex",
    "https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex",
)

REMOVED_SOURCE_MARKERS = (
    "x.com/OpenAI/status/2122750135608528984",
    "help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt",
    "help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers",
    "help.openai.com/en/articles/6950777-what-is-chatgpt-plus",
    "help.openai.com/en/articles/11989085-what-is-chatgpt-go",
    "https://chatgpt.com/pricing",
    "https://gpt20x.com/chatgpt-plus",
)

LIMIT_SENTENCE = (
    "Pro 100、Pro 200 和 Pro 500 在「工作」和 Codex 目前没有 5 小时限额，"
    "但仍有套餐内含用量和每周窗口，以英文帮助中心为准；Plus 仍有 5 小时窗口"
    "（2026-11-19 核对）。「目前」不代表无限使用。剩余量与重置时间以「设置 → 用量」为准。"
)

FORBIDDEN_PHRASES = (
    "Plus 和 Pro 在「工作」和 Codex 都有 5 小时窗口",
    "都有每周限制",
    "用量窗口和限制可能因套餐及产品变化",
    "不设 5 小时",
    "不设5小时",
    "Pro无5小时",
)

RELATED_TUTORIALS = (
    "https://amber-moose-14.github.io/chatgpt-daichong-guide/chatgpt-huiyuan-zenme-xuan-2026.html",
    "https://amber-moose-14.github.io/chatgpt-daichong-guide/chatgpt-plus-chongzhi-yuefu-2026.html",
    "https://amber-moose-14.github.io/chatgpt-daichong-guide/chatgpt-pro-chongzhi-edu-guize-2026.html",
    "https://amber-moose-14.github.io/chatgpt-daichong-guide/codex-daichong-yongliang-kaitong-2026.html",
    "https://amber-moose-14.github.io/chatgpt-daichong-guide/chatgpt-huiyuan-codex-gongxiang-2026.html",
)


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("article is missing front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise AssertionError("front matter is not closed")
    return text[4:end], text[end + 5 :]


def render_body(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=["tables", "sane_lists"],
        output_format="html",
    )


def is_main_site(href: str) -> bool:
    parsed = urlparse(href)
    return parsed.scheme == "https" and parsed.netloc.lower() in {"gpt20x.com", "www.gpt20x.com"}


def normalize_href(href: str) -> str:
    parsed = urlparse(href)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return f"{parsed.scheme}://{parsed.netloc}{path}"


class ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, str]] = []
        self.lists: list[dict] = []
        self._a_href: str | None = None
        self._a_parts: list[str] = []
        self._list_stack: list[dict] = []
        self._li_open = 0
        self._li_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "a":
            self._a_href = attr.get("href", "")
            self._a_parts = []
        elif tag in {"ol", "ul"}:
            self._list_stack.append({"type": tag, "items": []})
        elif tag == "li" and self._list_stack:
            self._li_open += 1
            if self._li_open == 1:
                self._li_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._a_href is not None:
            self.anchors.append((self._a_href, "".join(self._a_parts).strip()))
            self._a_href = None
            self._a_parts = []
        elif tag == "li" and self._li_open:
            self._li_open -= 1
            if self._li_open == 0 and self._list_stack:
                text = re.sub(r"\s+", " ", "".join(self._li_parts)).strip()
                self._list_stack[-1]["items"].append(text)
        elif tag in {"ol", "ul"} and self._list_stack:
            self.lists.append(self._list_stack.pop())

    def handle_data(self, data: str) -> None:
        if self._a_href is not None:
            self._a_parts.append(data)
        if self._li_open:
            self._li_parts.append(data)


def ordered_list_items(block: str) -> list[str]:
    items: list[str] = []
    expected = 1
    started = False
    for raw in block.splitlines():
        match = re.match(r"^(\d+)\. (.+)$", raw)
        if match:
            number = int(match.group(1))
            if number != expected:
                raise AssertionError(f"列表编号中断：期望 {expected}，实际 {number}：{raw}")
            items.append(match.group(2).strip())
            expected += 1
            started = True
            continue
        if started and raw.strip():
            break
    if not items:
        raise AssertionError("没有解析到有序列表")
    return items


def strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


class GPT62ArticleHTMLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = ARTICLE.read_text(encoding="utf-8")
        cls.front_matter, cls.body = split_front_matter(cls.raw)
        cls.html = render_body(cls.body)
        parser = ArticleHTMLParser()
        parser.feed(cls.html)
        cls.anchors = parser.anchors
        cls.lists = parser.lists
        cls.main_site = [(href, text) for href, text in cls.anchors if is_main_site(href)]

    def test_front_matter_keywords_unchanged(self) -> None:
        self.assertIn(f"title: {EXPECTED_TITLE}", self.front_matter)
        self.assertIn(f"description: {EXPECTED_DESCRIPTION}", self.front_matter)
        self.assertTrue(EXPECTED_TITLE.startswith("chatgpt会员"))
        self.assertTrue(EXPECTED_TITLE.endswith("｜GPT20X"))
        self.assertTrue(EXPECTED_DESCRIPTION.startswith("chatgpt会员"))
        self.assertIn(f"# {EXPECTED_TITLE}", self.body)
        self.assertEqual(ARTICLE.name, "chatgpt-huiyuan-gpt6-2-2026.md")

    def test_main_site_links_are_exactly_two(self) -> None:
        self.assertEqual(
            [(normalize_href(href), text) for href, text in self.main_site],
            [(normalize_href(href), text) for href, text in MAIN_SITE_LINKS],
        )
        for href, _text in self.anchors:
            parsed = urlparse(href)
            if parsed.netloc.lower() in {"gpt20x.com", "www.gpt20x.com"}:
                self.assertIn(parsed.path, {"", "/"})
        self.assertNotIn("https://gpt20x.com/chatgpt-plus", self.raw)
        self.assertNotIn("https://gpt20x.com/chatgpt-plus", self.html)

    def test_official_sources_are_three(self) -> None:
        start = self.html.find("<h2>10. 官方来源</h2>")
        end = self.html.find("相关教程", start)
        self.assertGreater(start, -1)
        self.assertGreater(end, start)
        section = self.html[start:end]
        parser = ArticleHTMLParser()
        parser.feed(section)
        hrefs = [normalize_href(href) for href, _text in parser.anchors]
        self.assertEqual(len(hrefs), 3)
        self.assertEqual(hrefs, [normalize_href(url) for url in OFFICIAL_SOURCES])
        source_lists = [item for item in parser.lists if item["type"] == "ul"]
        self.assertEqual(len(source_lists), 1, self.html[start:end])
        self.assertEqual(len(source_lists[0]["items"]), 3)
        self.assertIn("在「工作」和 Codex 中向 Plus、Pro、Enterprise、Edu 开放", source_lists[0]["items"][0])
        self.assertIn("2026-11-18 核对", source_lists[0]["items"][1])
        usage = source_lists[0]["items"][2]
        self.assertIn("2026-11-19 核对", usage)
        self.assertIn("目前在「工作」和 Codex 没有 5 小时限额", usage)
        self.assertIn("每周窗口", usage)
        self.assertIn("Plus 仍有 5 小时窗口", usage)
        self.assertIn("不代表无限使用", usage)
        self.assertIn("对应第 6 节", usage)
        self.assertNotIn("Pro 无 5 小时", section)
        for marker in REMOVED_SOURCE_MARKERS:
            self.assertNotIn(marker, self.raw)
            self.assertNotIn(marker, self.html)

    def test_related_pages_tutorials(self) -> None:
        related = [
            normalize_href(href)
            for href, _text in self.anchors
            if "amber-moose-14.github.io/chatgpt-daichong-guide/" in href
        ]
        self.assertGreaterEqual(len(related), 3)
        self.assertLessEqual(len(related), 6)
        self.assertEqual(related, [normalize_href(url) for url in RELATED_TUTORIALS])
        self.assertNotIn("chatgpt-huiyuan-gpt6-2-2026.html", " ".join(related))

    def test_approved_limit_wording_and_check_dates(self) -> None:
        combined = self.raw + "\n" + self.html
        for phrase in FORBIDDEN_PHRASES:
            self.assertNotIn(phrase, combined)
        self.assertIn(LIMIT_SENTENCE, self.raw)
        self.assertIn("目前没有 5 小时限额", self.raw)
        self.assertIn("不代表无限使用", self.raw)
        self.assertIn("Plus 仍有 5 小时窗口", self.raw)
        self.assertIn("每周窗口", self.raw)
        self.assertEqual(self.raw.count("不代表无限使用"), 2)
        self.assertEqual(self.raw.count("无限使用"), self.raw.count("不代表无限使用"))
        self.assertIn("非 OpenAI 官方内容", self.html)
        self.assertIn("最后更新：2026-11-19（修订日期）", self.raw)
        self.assertIn("英文页（2026-11-18 核对）", self.raw)
        self.assertIn("2026-11-18 核对时尚未同步", self.raw)
        self.assertIn("官方目前的说法（2026-11-18 核对）", self.raw)
        self.assertIn("2026-11-18 仍在更新", self.raw)
        self.assertIn("2026-11-18 核对中国页", self.raw)
        self.assertIn("（2026-11-18 核对：滚动开放范围", self.raw)
        self.assertIn("（2026-11-19 核对：Pro 100、Pro 200 和 Pro 500", self.raw)
        self.assertNotIn("最后更新：2026-11-18", self.raw)
        self.assertNotIn("我自己", self.raw)
        self.assertNotIn("亲测", self.raw)

    def test_ordered_lists_number_normally(self) -> None:
        toc_block = self.body.split("## 目录", 1)[1].split("## 1.", 1)[0]
        steps_block = self.body.split("多数情况不必重复付款。", 1)[1].split("## 9.", 1)[0]
        toc = ordered_list_items(toc_block)
        steps = ordered_list_items(steps_block)
        self.assertEqual(len(toc), 10)
        self.assertEqual(len(steps), 6)
        self.assertTrue(toc[0].startswith("先看结论"))
        self.assertTrue(toc[-1].startswith("官方来源"))
        self.assertIn("普通聊天", steps[0])

        ordered = [item for item in self.lists if item["type"] == "ol"]
        self.assertEqual(len(ordered), 2, [ (item["type"], len(item["items"])) for item in self.lists ])
        self.assertEqual(len(ordered[0]["items"]), 10)
        self.assertEqual(len(ordered[1]["items"]), 6)
        self.assertEqual(ordered[0]["items"], [strip_markdown(item) for item in toc])
        self.assertEqual(ordered[1]["items"], [strip_markdown(item) for item in steps])
        for item in self.lists:
            if item["type"] == "ol":
                self.assertGreaterEqual(len(item["items"]), 2)
                for index, text in enumerate(item["items"], start=1):
                    self.assertFalse(re.match(r"^\d+\.", text), f"列表项里又写了一遍编号：{index}. {text}")
        self.assertNotIn('value="1"', self.html)
        self.assertNotRegex(self.html, r"<ol>\s*<li>[^<]*</li>\s*</ol>\s*<ol>")


def report() -> str:
    raw = ARTICLE.read_text(encoding="utf-8")
    _front, body = split_front_matter(raw)
    html = render_body(body)
    parser = ArticleHTMLParser()
    parser.feed(html)
    main = [(href, text) for href, text in parser.anchors if is_main_site(href)]
    start = html.find("<h2>10. 官方来源</h2>")
    end = html.find("相关教程", start)
    source_parser = ArticleHTMLParser()
    source_parser.feed(html[start:end])
    related = [
        (href, text)
        for href, text in parser.anchors
        if "amber-moose-14.github.io/chatgpt-daichong-guide/" in href
    ]
    ordered = [item for item in parser.lists if item["type"] == "ol"]
    lines = [
        f"renderer: Python-Markdown {markdown.__version__} (tables, sane_lists)",
        f"article: {ARTICLE.name}",
        f"主站 href 数: {len(main)}",
    ]
    for index, (href, text) in enumerate(main, start=1):
        lines.append(f"  {index}. 锚文字={text} 目标={href}")
    lines.append(f"官方来源数: {len(source_parser.anchors)}")
    for index, (href, text) in enumerate(source_parser.anchors, start=1):
        lines.append(f"  {index}. 锚文字={text}")
        lines.append(f"     目标={href}")
    lines.append(f"相关 Pages 教程数: {len(related)}")
    for index, (href, text) in enumerate(related, start=1):
        lines.append(f"  {index}. {text} -> {href}")
    for index, item in enumerate(ordered, start=1):
        lines.append(f"有序列表 {index}: {len(item['items'])} 项，编号 1–{len(item['items'])}")
    lines.append("非 OpenAI 官方内容: 有" if "非 OpenAI 官方内容" in html else "非 OpenAI 官方内容: 无")
    lines.append(
        "最后更新：2026-11-19（修订日期）"
        if "最后更新：2026-11-19（修订日期）" in raw
        else "最后更新日期不符"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
    print("---")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GPT62ArticleHTMLTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
