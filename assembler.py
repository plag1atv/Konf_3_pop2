#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional


#внутреннее представление
@dataclass
class Instruction:
    opcode: str
    A: int
    B: int
    C: int


#регулировка языка
RE_LOAD_INDIRECT = re.compile(
    r"""^mem\[(\d+)\]\s*=\s*mem\[mem\[(\d+)\]\]\s*$"""
)

RE_BSWAP = re.compile(
    r"""^mem\[(\d+)\]\s*=\s*bswap\(\s*mem\[(\d+)\]\s*\)\s*$"""
)

RE_STORE = re.compile(
    r"""^mem\[(\d+)\]\s*=\s*mem\[(\d+)\]\s*$"""
)

RE_LOAD_CONST = re.compile(
    r"""^mem\[(\d+)\]\s*=\s*(\d+)\s*$"""
)

#в случае ошибки
class AssemblerError(Exception):
    pass


def parse_line(line: str, line_no: int) -> Optional[Instruction]:
    # Убирает комментарий
    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    #mem[C] = mem[mem[B]]  -> LOAD_INDIRECT (A=1)
    m = RE_LOAD_INDIRECT.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(
            opcode="LOAD_INDIRECT",
            A=1,
            B=b_addr,
            C=c_addr,
        )

    #mem[C] = bswap(mem[B]) -> BSWAP (A=3)
    m = RE_BSWAP.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(
            opcode="BSWAP",
            A=3,
            B=b_addr,
            C=c_addr,
        )

    #mem[C] = mem[B] -> STORE (A=13)
    m = RE_STORE.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(
            opcode="STORE",
            A=13,
            B=b_addr,
            C=c_addr,
        )

    #mem[B] = C -> LOAD_CONST (A=7)
    m = RE_LOAD_CONST.match(line)
    if m:
        b_addr = int(m.group(1))
        const = int(m.group(2))
        return Instruction(
            opcode="LOAD_CONST",
            A=7,
            B=b_addr,
            C=const,
        )

    raise AssemblerError(f"Не удалось разобрать строку {line_no}: {line!r}")

#читает по строчно, добавляет в список
def assemble(source_text: str) -> List[Instruction]:
    instructions: List[Instruction] = []
    for i, raw_line in enumerate(source_text.splitlines(), start=1):
        instr = parse_line(raw_line, i)
        if instr is not None:
            instructions.append(instr)
    return instructions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ассемблер для конфуп"
    )
    parser.add_argument("source", help="путь к исходному файлу с текстом программы")
    parser.add_argument("output", help="путь к файлу-результату")
    parser.add_argument(
        "--test",
        action="store_true",
        help="режим тестирования",
    )

    args = parser.parse_args()

    #читает исходник
    with open(args.source, "r", encoding="utf-8") as f:
        src = f.read()

    #ассемблирует в промежуточное представление
    instructions = assemble(src)

    #сохраняет в JSON
    ir = [asdict(instr) for instr in instructions]
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(ir, f, ensure_ascii=False, indent=2)

    #режим тестирования: вывод A,B,C как в спецификации
    if args.test:
        for instr in instructions:
            print(f"A={instr.A}, B={instr.B}, C={instr.C}")


if __name__ == "__main__":
    main()
