#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from typing import List, Optional
import re



#внутренне представление
@dataclass
class Instruction:
    opcode: str
    A: int
    B: int
    C: int


RE_LOAD_INDIRECT = re.compile(r"^mem\[(\d+)\]\s*=\s*mem\[mem\[(\d+)\]\]\s*$")
RE_BSWAP         = re.compile(r"^mem\[(\d+)\]\s*=\s*bswap\(\s*mem\[(\d+)\]\s*\)\s*$")
RE_STORE         = re.compile(r"^mem\[(\d+)\]\s*=\s*mem\[(\d+)\]\s*$")
RE_LOAD_CONST    = re.compile(r"^mem\[(\d+)\]\s*=\s*(\d+)\s*$")


class AssemblerError(Exception):
    pass


def parse_line(line: str, line_no: int) -> Optional[Instruction]:
    #убрирает комментарий
    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    # mem[C] = mem[mem[B]] -> LOAD_INDIRECT (A = 1)
    m = RE_LOAD_INDIRECT.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(opcode="LOAD_INDIRECT", A=1, B=b_addr, C=c_addr)

    # mem[C] = bswap(mem[B]) -> BSWAP (A = 3)
    m = RE_BSWAP.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(opcode="BSWAP", A=3, B=b_addr, C=c_addr)

    # mem[C] = mem[B] -> STORE (A = 13)
    m = RE_STORE.match(line)
    if m:
        c_addr = int(m.group(1))
        b_addr = int(m.group(2))
        return Instruction(opcode="STORE", A=13, B=b_addr, C=c_addr)

    # mem[B] = C -> LOAD_CONST (A = 7)
    m = RE_LOAD_CONST.match(line)
    if m:
        b_addr = int(m.group(1))
        const = int(m.group(2))
        return Instruction(opcode="LOAD_CONST", A=7, B=b_addr, C=const)

    raise AssemblerError(f"Не удалось разобрать строку {line_no}: {line!r}")


def assemble_to_ir(source_text: str) -> List[Instruction]:
    instructions: List[Instruction] = []
    for i, raw_line in enumerate(source_text.splitlines(), start=1):
        instr = parse_line(raw_line, i)
        if instr is not None:
            instructions.append(instr)
    return instructions

#IR -> машинный код
def encode_instruction(instr: Instruction) -> bytes:
    A, B, C = instr.A, instr.B, instr.C

    # A: 4 бита
    if not (0 <= A < (1 << 4)):
        raise ValueError(f"Недопустимое A={A}, нужно 0..15")

    if instr.opcode == "LOAD_CONST":
        # B: 14 бит, C: до 25 бит
        if not (0 <= B < (1 << 14)):
            raise ValueError(f"Недопустимое B={B} для LOAD_CONST, нужно 0..{(1<<14)-1}")
        if not (0 <= C < (1 << 25)):
            raise ValueError(f"Недопустимое C={C} для LOAD_CONST, нужно 0..{(1<<25)-1}")
    else:
        # B и C по 14 бит
        if not (0 <= B < (1 << 14)):
            raise ValueError(f"Недопустимое B={B}, нужно 0..{(1<<14)-1}")
        if not (0 <= C < (1 << 14)):
            raise ValueError(f"Недопустимое C={C}, нужно 0..{(1<<14)-1}")

    # Упаковка: общая формула для всех четырёх команд
    code = A | (B << 4) | (C << 18)

    # 7 байт little-endian
    out = bytearray(7)
    for i in range(7):
        out[i] = (code >> (8 * i)) & 0xFF
    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ассемблер УВМ, вариант 7 (этап 2: формирование машинного кода)."
    )
    parser.add_argument("source", help="Путь к исходному файлу с текстом программы")
    parser.add_argument("output", help="Путь к бинарному файлу-результату")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Режим тестирования: печатать байты, как в спецификации УВМ",
    )

    args = parser.parse_args()

    #читает алгебраический исходник
    with open(args.source, "r", encoding="utf-8") as f:
        src = f.read()

    #текст -> IR
    instructions = assemble_to_ir(src)

    #IR -> байты
    binary = bytearray()
    for instr in instructions:
        binary += encode_instruction(instr)

    #записывает бинарник
    with open(args.output, "wb") as f:
        f.write(binary)

    #размер файла
    size_bytes = len(binary)
    print(f"Размер двоичного файла: {size_bytes} байт")

    #режим теста: распечатать байты каждой команды
    if args.test:
        offset = 0
        for idx, instr in enumerate(instructions, start=1):
            chunk = binary[offset:offset + 7]
            offset += 7
            hex_bytes = ", ".join(f"0x{b:02X}" for b in chunk)
            print(f"{idx}: {hex_bytes}")


if __name__ == "__main__":
    main()
