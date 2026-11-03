"""Read and patch ActionScript 2 byte code in place: a boolean in one branch, a string in the
constant pool. Same length always; nothing is recompiled.

A class's code sits in a DoInitAction tag (build_phone_history.class_actions finds it). Its
actions are walked one by one, nested function bodies included (a DefineFunction2's length
covers its header only; the body follows as ordinary actions), so a site inside a method can be
found by the instructions round it, the way build_display finds its numbers by their names.
"""
from __future__ import annotations

import struct

PUSH, POOL, GET_MEMBER, SET_MEMBER, NOT, IF, JUMP = 0x96, 0x88, 0x4E, 0x4F, 0x12, 0x9D, 0x99
BLOCKS = {0x8F: "Try", 0x94: "With", 0x8A: "WaitForFrame", 0x8D: "WaitForFrame2", 0x9B: "DefineFunction", 0x8E: "DefineFunction2"}
PUSH_SIZES = {1: 4, 2: 0, 3: 0, 4: 1, 5: 1, 6: 8, 7: 4, 8: 1, 9: 2}


def actions(code: bytes):
    """(offset, opcode, operand bytes) for every action in the code."""
    p = 0
    while p < len(code):
        op = code[p]
        if op == 0:
            p += 1
            continue
        if op < 0x80:
            yield p, op, b""
            p += 1
            continue
        length = struct.unpack_from("<H", code, p + 1)[0]
        yield p, op, code[p + 3:p + 3 + length]
        p += 3 + length


def pool(code: bytes) -> tuple[int, list[str]]:
    """(offset of the ConstantPool action, its strings)."""
    for offset, op, data in actions(code):
        if op == POOL:
            out, q = [], 2
            for _ in range(struct.unpack_from("<H", data)[0]):
                end = data.index(b"\0", q)
                out.append(data[q:end].decode("latin1"))
                q = end + 1
            return offset, out
    raise SystemExit("no constant pool in this class")


def push_items(data: bytes, strings: list[str]) -> list:
    """A Push's operands: pool strings and inline strings as str, booleans as bool, registers
    as ("r", n), other numbers as None."""
    items, q = [], 0
    while q < len(data):
        kind = data[q]
        q += 1
        if kind == 0:
            end = data.index(b"\0", q)
            items.append(data[q:end].decode("latin1"))
            q = end + 1
            continue
        if kind == 8:
            items.append(strings[data[q]])
        elif kind == 9:
            items.append(strings[struct.unpack_from("<H", data, q)[0]])
        elif kind == 5:
            items.append(bool(data[q]))
        elif kind == 4:
            items.append(("r", data[q]))
        else:
            items.append(None)
        q += PUSH_SIZES[kind]
    return items


def branch_target(offset: int, data: bytes) -> int:
    """Where a Jump or If at `offset` goes: its signed offset counts from the next action."""
    return offset + 5 + struct.unpack_from("<h", data)[0]


def branch_boolean(code: bytes, opener: str, member: str, prop: str) -> int:
    """The offset of the boolean byte in the one `Push <member> GetMember Push <prop>, true
    SetMember` inside the branch opened by the one `Push .. <opener> GetMember Not If` in the
    code: the If's fall-through, from the action after it up to its target (the else arm and
    whatever follows are not searched). Exactly one opener and exactly one such push."""
    _, strings = pool(code)
    seq = list(actions(code))
    opened = None
    for i in range(len(seq) - 3):
        (_, op, d), (_, op2, _), (_, op3, _), (o4, op4, d4) = seq[i:i + 4]
        if op == PUSH and push_items(d, strings)[-1:] == [opener] and (op2, op3, op4) == (GET_MEMBER, NOT, IF):
            if opened is not None:
                raise SystemExit(f"more than one `{opener} ... Not If`: not the class this was made for")
            opened, start, stop = i + 4, o4 + 5, branch_target(o4, d4)
    if opened is None:
        raise SystemExit(f"no `{opener} ... Not If`: not the class this was made for")
    if stop <= start or stop > len(code):
        raise SystemExit(f"the `{opener}` branch does not run forward inside the code: not the class this was made for")
    hits = []
    for i in range(opened, len(seq) - 3):
        (o, op, d), (_, op2, _), (o3, op3, d3), (o4, op4, _) = seq[i:i + 4]
        if o4 + 1 > stop:
            break
        if op == PUSH and push_items(d, strings) == [member] and op2 == GET_MEMBER and op3 == PUSH \
                and push_items(d3, strings) == [prop, True] and op4 == SET_MEMBER:
            hits.append(o3 + 3 + len(d3) - 1)  # the boolean's value is the Push's last byte
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} `{member}.{prop} = true` in the `{opener}` branch, not one: not the class this was made for")
    return hits[0]


def set_boolean(code: bytes, offset: int, value: bool) -> bytes:
    """The code with the boolean at `offset` set; it must be a boolean push operand now."""
    if not any(op == PUSH and o + 3 <= offset < o + 3 + len(d) and d[offset - o - 3 - 1] == 5
               for o, op, d in actions(code)):
        raise SystemExit("not a boolean push operand")
    patched = bytearray(code)
    patched[offset] = 1 if value else 0
    return bytes(patched)


def replace_strings(code: bytes, changes: dict[bytes, bytes]) -> bytes:
    """The code with each constant-pool string replaced. Each old string must occur exactly
    once in the pool (identical strings share one entry, so every use of it changes). A
    replacement of another length changes the pool record's and the code's length; that is
    allowed only when the pool is the code's first action and nothing spans its end: no Jump or
    If may land before the end of the pool, and no Try, With, WaitForFrame or function body may
    start before it (their sizes are written in their headers). Pushes name pool entries by
    index, which does not change."""
    offset, before = pool(code)
    length = struct.unpack_from("<H", code, offset + 1)[0]  # the count and the strings
    count, entries = code[offset + 3:offset + 5], code[offset + 5:offset + 3 + length]
    if any(len(old) != len(new) for old, new in changes.items()):
        pool_end = offset + 3 + length
        if offset != 0:
            raise SystemExit("a string of another length needs the constant pool first in the code")
        for at, op, data in actions(code):
            if op in (JUMP, IF) and branch_target(at, data) < pool_end:
                raise SystemExit(f"a branch at {at} lands inside the constant pool: its length cannot change")
            if op in BLOCKS and at < pool_end:
                raise SystemExit(f"a {BLOCKS[op]} block spans the constant pool: its length cannot change")
    for old, new in changes.items():
        if not old.endswith(b"\0") or not new.endswith(b"\0"):
            raise ValueError("replacement strings must be NUL-terminated")
        if entries.split(b"\0").count(old[:-1]) != 1:
            raise SystemExit(f"{old[:-1]!r} is not once in the constant pool: not the class this was made for")
        entries = b"\0".join(new[:-1] if e == old[:-1] else e for e in entries.split(b"\0"))
    patched = code[:offset + 1] + struct.pack("<H", len(entries) + 2) + count + entries + code[offset + 3 + length:]
    wanted = {old[:-1].decode("latin1"): new[:-1].decode("latin1") for old, new in changes.items()}
    if pool(patched)[1] != [wanted.get(s, s) for s in before]:
        raise SystemExit("the constant pool did not read back as written")
    return patched
