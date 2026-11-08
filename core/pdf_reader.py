# -*- coding: utf-8 -*-
"""河小智 · 纯标准库 PDF 文本提取。

不依赖第三方库，支持：

- ``FlateDecode``（zlib）与未压缩内容流；
- 通过扫描 ``N G obj ... endobj`` 兜底解析，不依赖 xref 偏移；
- 对象流 ``ObjStm``（Word / 浏览器导出的 PDF 常见）；
- 内容流文本操作符 ``Tj``、``TJ``、``'``、``"``，以及 ``Td/TD/T*/Tm`` 换行；
- **ToUnicode CMap**（``bfchar`` / ``bfrange``，含 UTF-16 代理对）与 Identity-H，
  从而把中文 PDF 正确还原为中文，而不是 CID 数字或乱码；
- WinAnsi / cp1252 简单字体兜底。

``extract()`` 永不抛异常；``decode_text_file()`` 用于 .txt / .md 上传。
"""

from __future__ import annotations

import re
import zlib

_OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")
_FONT_BLOCK_RE = re.compile(rb"/Font\s*<<(.*?)>>", re.S)
_FONT_REF_RE = re.compile(rb"/([^\s/<>\[\](){}]+)\s+(\d+)\s+0\s+R")
_NUMBER_RE = re.compile(rb"^[+-]?(\d+(\.\d*)?|\.\d+)$")
_WHITESPACE = b" \t\r\n\f\x00"


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def is_pdf(data: bytes) -> bool:
    return bool(data) and data[:5] == b"%PDF-"


def decode_text_file(data: bytes) -> str:
    """按 utf-8-sig → utf-8 → gbk → gb18030 顺序解码文本文件。"""
    if not data:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", "replace")


def _head(body: bytes) -> bytes:
    """去掉 stream 数据，只保留对象字典部分。"""
    pos = body.find(b"stream")
    return body if pos == -1 else body[:pos]


def _split_stream(body: bytes) -> tuple[bytes, bytes]:
    pos = body.find(b"stream")
    if pos == -1:
        return body, b""
    dict_part = body[:pos]
    start = pos + len(b"stream")
    if body[start : start + 2] == b"\r\n":
        start += 2
    elif body[start : start + 1] in (b"\n", b"\r"):
        start += 1
    end = body.find(b"endstream", start)
    if end == -1:
        end = len(body)
    stream = body[start:end]
    if stream.endswith(b"\r\n"):
        stream = stream[:-2]
    elif stream.endswith(b"\n") or stream.endswith(b"\r"):
        stream = stream[:-1]
    return dict_part, stream


def _decode_stream(dict_part: bytes, stream: bytes) -> bytes:
    if not stream:
        return b""
    filter_match = re.search(rb"/Filter\s*(\[[^\]]*\]|/[A-Za-z0-9]+)", dict_part)
    filters = filter_match.group(1) if filter_match else b""
    if b"FlateDecode" in filters or not filters:
        for attempt in (
            lambda raw: zlib.decompress(raw),
            lambda raw: zlib.decompressobj().decompress(raw),
            lambda raw: zlib.decompress(raw, -15),
        ):
            try:
                decoded = attempt(stream)
                if decoded:
                    return decoded
            except Exception:
                continue
        if b"FlateDecode" in filters:
            return b""
    if b"ASCIIHexDecode" in filters:
        try:
            cleaned = re.sub(rb"\s+", b"", stream).rstrip(b">")
            return bytes.fromhex(cleaned.decode("ascii", "ignore"))
        except Exception:
            return b""
    return stream


def _int_param(dict_part: bytes, name: bytes) -> int | None:
    match = re.search(re.escape(name) + rb"\s+(\d+)", dict_part)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _to_float(raw) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# 对象解析（含 ObjStm）
# --------------------------------------------------------------------------- #
def _parse_objects(data: bytes) -> dict[int, bytes]:
    objects: dict[int, bytes] = {}
    for match in _OBJ_RE.finditer(data):
        number = int(match.group(1))
        start = match.end()
        end = data.find(b"endobj", start)
        if end == -1:
            end = len(data)
        objects[number] = data[start:end]
    return objects


def _expand_object_streams(objects: dict[int, bytes]) -> None:
    extra: dict[int, bytes] = {}
    for body in list(objects.values()):
        dict_part, stream = _split_stream(body)
        if not stream or b"/ObjStm" not in dict_part:
            continue
        content = _decode_stream(dict_part, stream)
        if not content:
            continue
        count = _int_param(dict_part, b"/N")
        first = _int_param(dict_part, b"/First")
        if not count or first is None or first <= 0:
            continue
        header = content[:first].split()
        for index in range(min(count, len(header) // 2)):
            try:
                number = int(header[index * 2])
                offset = int(header[index * 2 + 1])
            except (ValueError, IndexError):
                continue
            next_offset = None
            if index * 2 + 3 < len(header):
                try:
                    next_offset = int(header[index * 2 + 3])
                except ValueError:
                    next_offset = None
            start = first + offset
            end = first + next_offset if next_offset is not None else len(content)
            if 0 <= start < end <= len(content):
                extra.setdefault(number, content[start:end])
    for number, body in extra.items():
        objects.setdefault(number, body)


# --------------------------------------------------------------------------- #
# ToUnicode CMap
# --------------------------------------------------------------------------- #
def _utf16_hex_to_text(hex_string: str) -> str:
    try:
        raw = bytes.fromhex(hex_string)
    except ValueError:
        return ""
    if len(raw) % 2:
        raw = raw[:-1]
    try:
        return raw.decode("utf-16-be")
    except UnicodeDecodeError:
        try:
            return raw.decode("utf-16-be", "ignore")
        except Exception:
            return ""


def _parse_cmap(content: bytes) -> dict[int, str]:
    text = content.decode("latin-1", "ignore")
    mapping: dict[int, str] = {}

    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for source, target in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            try:
                mapping[int(source, 16)] = _utf16_hex_to_text(target)
            except ValueError:
                continue

    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        pattern = re.compile(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(?:<([0-9A-Fa-f]+)>|\[(.*?)\])",
            re.S,
        )
        for match in pattern.finditer(block):
            try:
                start = int(match.group(1), 16)
                end = int(match.group(2), 16)
            except ValueError:
                continue
            if end < start:
                continue
            if match.group(3):
                base_text = _utf16_hex_to_text(match.group(3))
                if not base_text:
                    continue
                prefix = base_text[:-1]
                base_code = ord(base_text[-1])
                for offset, code in enumerate(range(start, end + 1)):
                    try:
                        mapping[code] = prefix + chr(base_code + offset)
                    except (ValueError, OverflowError):
                        continue
            elif match.group(4):
                targets = re.findall(r"<([0-9A-Fa-f]+)>", match.group(4))
                for offset, target in enumerate(targets):
                    if start + offset > end:
                        break
                    mapping[start + offset] = _utf16_hex_to_text(target)
    return {code: value for code, value in mapping.items() if value}


def _font_info(objects: dict[int, bytes], number: int) -> tuple[dict[int, str], bool] | None:
    body = objects.get(number)
    if not body:
        return None
    dict_part = _head(body)
    to_unicode = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", dict_part)
    cmap: dict[int, str] = {}
    if to_unicode:
        cmap_body = objects.get(int(to_unicode.group(1)), b"")
        if cmap_body:
            cmap_dict, cmap_stream = _split_stream(cmap_body)
            raw = _decode_stream(cmap_dict, cmap_stream) if cmap_stream else cmap_body
            cmap = _parse_cmap(raw or b"")
    two_byte = bool(re.search(rb"/Encoding\s*/Identity-[HV]", dict_part))
    if cmap and any(code > 255 for code in cmap):
        two_byte = True
    if not cmap and not two_byte:
        # 简单字体（WinAnsi / MacRoman）交给 cp1252 兜底
        return ({}, False)
    return (cmap, two_byte)


def _merge_fonts(fonts: dict[str, tuple[dict[int, str], bool]]) -> tuple[dict[int, str], bool]:
    merged: dict[int, str] = {}
    two_byte = False
    for cmap, font_two_byte in fonts.values():
        two_byte = two_byte or font_two_byte
        for code, value in cmap.items():
            merged.setdefault(code, value)
    return merged, two_byte


# --------------------------------------------------------------------------- #
# 页面定位
# --------------------------------------------------------------------------- #
def _walk_pages(
    objects: dict[int, bytes],
    number: int,
    output: list[tuple[int, bytes]],
    seen: set[int],
) -> None:
    if number in seen:
        return
    seen.add(number)
    body = objects.get(number)
    if not body:
        return
    if re.search(rb"/Type\s*/Page\b", body):
        output.append((number, body))
        return
    kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
    if kids:
        for ref in re.findall(rb"(\d+)\s+\d+\s+R", kids.group(1)):
            _walk_pages(objects, int(ref), output, seen)


def _ordered_pages(objects: dict[int, bytes]) -> list[tuple[int, bytes]]:
    for body in objects.values():
        if re.search(rb"/Type\s*/Catalog\b", body):
            pages_ref = re.search(rb"/Pages\s+(\d+)\s+0\s+R", body)
            if pages_ref:
                output: list[tuple[int, bytes]] = []
                _walk_pages(objects, int(pages_ref.group(1)), output, set())
                if output:
                    return output
    # 兜底：按对象编号顺序
    pages = [
        (number, body)
        for number, body in sorted(objects.items())
        if re.search(rb"/Type\s*/Page\b", body)
    ]
    return pages


def _page_contents(body: bytes, objects: dict[int, bytes]) -> bytes:
    match = re.search(rb"/Contents\s*(\[[^\]]*\]|\d+\s+\d+\s+R)", body)
    if not match:
        return b""
    refs = [int(value) for value in re.findall(rb"(\d+)\s+\d+\s+R", match.group(1))]
    chunks: list[bytes] = []
    for ref in refs:
        stream_body = objects.get(ref)
        if not stream_body:
            continue
        dict_part, stream = _split_stream(stream_body)
        if stream:
            chunks.append(_decode_stream(dict_part, stream))
    return b"\n".join(chunks)


def _page_fonts(body: bytes, objects: dict[int, bytes]) -> dict[str, tuple[dict[int, str], bool]]:
    resources = body
    resource_ref = re.search(rb"/Resources\s+(\d+)\s+0\s+R", body)
    if resource_ref:
        resources = objects.get(int(resource_ref.group(1)), b"")
    fonts: dict[str, tuple[dict[int, str], bool]] = {}
    for block in _FONT_BLOCK_RE.finditer(resources):
        for name, ref in _FONT_REF_RE.findall(block.group(1)):
            info = _font_info(objects, int(ref))
            if info is not None:
                fonts[name.decode("latin-1", "ignore")] = info
    return fonts


def _collect_fonts(objects: dict[int, bytes]) -> dict[str, tuple[dict[int, str], bool]]:
    fonts: dict[str, tuple[dict[int, str], bool]] = {}
    for body in objects.values():
        for block in _FONT_BLOCK_RE.finditer(_head(body)):
            for name, ref in _FONT_REF_RE.findall(block.group(1)):
                info = _font_info(objects, int(ref))
                if info is not None:
                    fonts[name.decode("latin-1", "ignore")] = info
    return fonts


# --------------------------------------------------------------------------- #
# 内容流解析
# --------------------------------------------------------------------------- #
def _read_literal(content: bytes, start: int) -> tuple[bytes, int]:
    """读取 PDF 字面量字符串 (...)，处理转义与括号嵌套。"""
    output = bytearray()
    depth = 1
    index = start + 1
    length = len(content)
    while index < length:
        char = content[index : index + 1]
        if char == b"\\":
            index += 1
            if index >= length:
                break
            escape = content[index : index + 1]
            if escape in (b"n", b"r", b"t", b"b", b"f"):
                output.extend({b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}[escape])
                index += 1
            elif escape in (b"(", b")", b"\\"):
                output.extend(escape)
                index += 1
            elif escape in (b"\n", b"\r"):
                index += 1
                if escape == b"\r" and content[index : index + 1] == b"\n":
                    index += 1
            elif escape.isdigit():
                octal = bytearray()
                while index < length and len(octal) < 3 and content[index : index + 1].isdigit():
                    octal.extend(content[index : index + 1])
                    index += 1
                try:
                    output.append(int(octal, 8) & 0xFF)
                except ValueError:
                    pass
            else:
                output.extend(escape)
                index += 1
            continue
        if char == b"(":
            depth += 1
            output.extend(char)
            index += 1
            continue
        if char == b")":
            depth -= 1
            if depth == 0:
                index += 1
                break
            output.extend(char)
            index += 1
            continue
        output.extend(char)
        index += 1
    return bytes(output), index


def _hex_to_bytes(value: bytes) -> bytes:
    cleaned = re.sub(rb"\s+", b"", value)
    if not cleaned:
        return b""
    if len(cleaned) % 2:
        cleaned += b"0"
    try:
        return bytes.fromhex(cleaned.decode("ascii", "ignore"))
    except ValueError:
        return b""


def _decode_text_bytes(data: bytes, font: tuple[dict[int, str], bool]) -> str:
    cmap, two_byte = font
    if two_byte:
        output = []
        for index in range(0, len(data) - 1, 2):
            code = (data[index] << 8) | data[index + 1]
            value = cmap.get(code)
            if value is None:
                value = cmap.get(data[index], "")
            if value is None:
                value = ""
            output.append(value)
        if len(data) % 2:
            output.append(cmap.get(data[-1], ""))
        return "".join(output)
    if cmap:
        return "".join(
            cmap.get(byte, chr(byte) if 32 <= byte < 127 else "") for byte in data
        )
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        return data.decode("latin-1", "ignore")


def _extract_text_from_content(
    content: bytes,
    fonts: dict[str, tuple[dict[int, str], bool]],
) -> str:
    if not content:
        return ""
    merged_font = _merge_fonts(fonts)
    current_font = merged_font
    current_y: float | None = None
    output: list[str] = []
    stack: list[tuple[str, object]] = []

    def newline() -> None:
        if output and not output[-1].endswith("\n"):
            output.append("\n")

    def emit(value: str) -> None:
        if value:
            output.append(value)

    index = 0
    length = len(content)
    while index < length:
        char = content[index : index + 1]
        if char in (b" ", b"\t", b"\r", b"\n", b"\f", b"\x00"):
            index += 1
            continue
        if char == b"%":
            line_end = content.find(b"\n", index)
            index = length if line_end == -1 else line_end + 1
            continue
        if char == b"(":
            value, index = _read_literal(content, index)
            stack.append(("str", value))
            continue
        if char == b"<":
            if content[index : index + 2] == b"<<":
                depth = 0
                cursor = index
                while cursor < length:
                    if content[cursor : cursor + 2] == b"<<":
                        depth += 1
                        cursor += 2
                    elif content[cursor : cursor + 2] == b">>":
                        depth -= 1
                        cursor += 2
                        if depth == 0:
                            break
                    else:
                        cursor += 1
                index = cursor
                continue
            close = content.find(b">", index + 1)
            if close == -1:
                close = length
            stack.append(("str", _hex_to_bytes(content[index + 1 : close])))
            index = close + 1
            continue
        if char == b"[":
            stack.append(("arr_start", None))
            index += 1
            continue
        if char == b"]":
            items: list[object] = []
            while stack and stack[-1][0] != "arr_start":
                items.append(stack.pop()[1])
            if stack and stack[-1][0] == "arr_start":
                stack.pop()
            stack.append(("arr", list(reversed(items))))
            index += 1
            continue
        if char == b"/":
            cursor = index + 1
            while cursor < length and content[cursor : cursor + 1] not in b" \t\r\n\f[]<>()/%{}":
                cursor += 1
            stack.append(("name", content[index + 1 : cursor].decode("latin-1", "ignore")))
            index = cursor
            continue
        if char in (b"{", b"}"):
            index += 1
            continue

        cursor = index
        while cursor < length and content[cursor : cursor + 1] not in b" \t\r\n\f[]<>()/%{}":
            cursor += 1
        token = content[index:cursor]
        index = cursor if cursor > index else index + 1
        if not token:
            continue
        if _NUMBER_RE.match(token):
            stack.append(("num", token))
            continue

        operator = token
        if operator == b"Tf":
            if len(stack) >= 2 and stack[-2][0] == "name":
                name = str(stack[-2][1])
                current_font = fonts.get(name, merged_font)
        elif operator == b"Tj":
            if stack and stack[-1][0] == "str":
                emit(_decode_text_bytes(stack[-1][1], current_font))  # type: ignore[arg-type]
        elif operator == b"'":
            newline()
            if stack and stack[-1][0] == "str":
                emit(_decode_text_bytes(stack[-1][1], current_font))  # type: ignore[arg-type]
        elif operator == b'"':
            newline()
            if stack and stack[-1][0] == "str":
                emit(_decode_text_bytes(stack[-1][1], current_font))  # type: ignore[arg-type]
        elif operator == b"TJ":
            if stack and stack[-1][0] == "arr":
                for item in stack[-1][1]:  # type: ignore[union-attr]
                    if isinstance(item, bytes):
                        emit(_decode_text_bytes(item, current_font))
                    else:
                        displacement = _to_float(item)
                        if displacement is not None and displacement < -120:
                            emit(" ")
        elif operator in (b"Td", b"TD"):
            if len(stack) >= 2:
                ty = _to_float(stack[-1][1])
                if ty is not None and abs(ty) > 0.5:
                    newline()
        elif operator == b"T*":
            newline()
        elif operator == b"Tm":
            if len(stack) >= 6:
                y = _to_float(stack[-1][1])
                if y is not None:
                    if current_y is not None and abs(y - current_y) > 1.0:
                        newline()
                    current_y = y
        stack = []

    return "".join(output)


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("﻿", "").replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"[ \t 　]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# 对外接口
# --------------------------------------------------------------------------- #
def extract(data: bytes, max_pages: int = 30, max_chars: int = 200000) -> dict:
    """提取 PDF 文本；永不抛异常。"""
    result: dict = {
        "ok": False,
        "engine": "none",
        "pages": [],
        "page_count": 0,
        "chars": 0,
        "encrypted": False,
        "scanned": False,
        "warnings": [],
        "error": "",
    }

    if not data:
        result["error"] = "文件是空的。"
        return result
    if len(data) > 50 * 1024 * 1024:
        result["error"] = "文件超过 50MB，请上传更小的 PDF。"
        return result

    encrypted = bool(re.search(rb"/Encrypt\b", data))
    result["encrypted"] = encrypted

    if not is_pdf(data):
        result["error"] = "这不是有效的 PDF 文件。"
        return result

    try:
        objects = _parse_objects(data)
        _expand_object_streams(objects)
        result["engine"] = "pdf"

        pages = _ordered_pages(objects)
        if not pages:
            # 没有标准页面树时，扫描所有包含文本操作符的内容流
            pages = []
            for number, body in sorted(objects.items()):
                dict_part, stream = _split_stream(body)
                if not stream:
                    continue
                decoded = _decode_stream(dict_part, stream)
                if b"BT" in decoded and (b"Tj" in decoded or b"TJ" in decoded):
                    pages.append((number, body))

        total_pages = len(pages)
        result["page_count"] = total_pages
        global_fonts = _collect_fonts(objects)

        extracted_pages: list[dict] = []
        total_chars = 0
        for page_number, body in pages[: max(1, int(max_pages))]:
            fonts = _page_fonts(body, objects) or global_fonts
            content = _page_contents(body, objects)
            if not content:
                dict_part, stream = _split_stream(body)
                if stream:
                    content = _decode_stream(dict_part, stream)
            if not content:
                continue
            text = _clean_text(_extract_text_from_content(content, fonts))
            remaining = max_chars - total_chars
            if remaining <= 0:
                break
            text = text[:remaining]
            if not text:
                continue
            extracted_pages.append({"no": page_number, "text": text})
            total_chars += len(text)
            if total_chars >= max_chars:
                break

        result["pages"] = extracted_pages
        result["chars"] = total_chars
        result["scanned"] = total_chars == 0
        result["ok"] = True

        if total_chars == 0:
            if encrypted:
                result["ok"] = False
                result["error"] = "该 PDF 已加密，无法提取文字，请上传未加密版本。"
            else:
                result["warnings"].append("没有检测到文字层（可能是扫描件 / 图片版 PDF）。")
        elif encrypted:
            result["warnings"].append("该 PDF 已加密，仅提取到部分可读文字。")
        return result
    except Exception as exc:  # pragma: no cover - 任何异常都转成用户可读提示
        result["ok"] = False
        result["error"] = f"PDF 解析失败：{exc}"
        return result


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as handle:
            payload = handle.read()
        info = extract(payload)
        print({key: info[key] for key in ("ok", "chars", "page_count", "scanned", "error")})
        for page in info["pages"][:3]:
            print(f"--- 第 {page['no']} 页 ---")
            print(page["text"][:500])
    else:
        print("用法: python -m core.pdf_reader <file.pdf>")
