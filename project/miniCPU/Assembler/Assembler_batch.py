import argparse
from typing import List, Tuple, Optional

import instructions


def preprocess_instruction(line: str) -> Tuple[str, List[str]]:
    """
    Turn an assembly line into (mnemonic, operands[]).

    Supports:
      - commas: addi x1, x0, 1
      - load/store addressing: lw x1, 0(x2)  -> ["x1","0","x2"]
    """
    parts = line.replace(",", "").replace("(", " ").replace(")", "").split()
    if not parts:
        raise ValueError("Empty instruction")
    mnemonic = parts[0]
    operands = parts[1:]
    return mnemonic, operands


def register_to_binary(register: str) -> str:
    if not register.startswith("x"):
        raise ValueError(f"Invalid register name: {register}")
    try:
        reg_num = int(register[1:])
    except Exception:
        raise ValueError(f"Invalid register name: {register}")
    if not (0 <= reg_num <= 31):
        raise ValueError(f"Register out of range x0-x31: {register}")
    return format(reg_num, "05b")


def immediate_to_binary(immediate: str, bits: int) -> str: #please learn: can not read this yet
    imm = int(immediate, 0)  # allow decimal and 0x.. forms
    if imm < 0:
        imm = (1 << bits) + imm
    return format(imm & ((1 << bits) - 1), f"0{bits}b")


def bin_to_hex32(bin_str: str) -> str:
    """32-bit binary string -> 8-hex-digit string (no 0x prefix)."""
    if len(bin_str) != 32:
        raise ValueError(f"Expected 32-bit machine code, got {len(bin_str)} bits")
    return format(int(bin_str, 2), "08x")


def assemble_to_machine_code(assembly_instruction: str) -> dict:
    mnemonic, operand = preprocess_instruction(assembly_instruction)
    inst = instructions.INSTRUCTIONS_SET.get(mnemonic)
    if inst is None:
        raise ValueError(f"Unknown mnemonic: {mnemonic}")

    opcode = inst["opcode"]
    inst_type = inst["type"]

    if inst_type == "R":
        # R-type: mnemonic rd, rs1, rs2
        rd, rs1, rs2 = operand
        machine_code = (
            f"{inst['funct7']}"
            f"{register_to_binary(rs2)}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    elif inst_type == "I1":
        # I-type: addi/andi/ori 是 rd, rs1, imm
        # lw 在 preprocess 后是 rd, imm, rs1
        if mnemonic == "lw":
            rd, imm, rs1 = operand
        else:
            rd, rs1, imm = operand
        imm_binary = immediate_to_binary(imm, 12)
        machine_code = (
            f"{imm_binary}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )


    elif inst_type == "S":
        # S-type: sw rs2, imm(rs1) -> preprocess gives [rs2, imm, rs1]
        rs2, imm, rs1 = operand
        imm_binary = immediate_to_binary(imm, 12)
        machine_code = (
            f"{imm_binary[:7]}"
            f"{register_to_binary(rs2)}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{imm_binary[7:]}"
            f"{opcode}"
        )

    elif inst_type == "B":
        # B-type: bne rs1, rs2, imm
        rs1, rs2, imm = operand
        imm_binary = immediate_to_binary(imm, 13)  # includes sign bit
        # imm[12] imm[10:5] rs2 rs1 funct3 imm[4:1] imm[11] opcode
        machine_code = (
            f"{imm_binary[0]}"
            f"{imm_binary[2:8]}"
            f"{register_to_binary(rs2)}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{imm_binary[8:12]}"
            f"{imm_binary[1]}"
            f"{opcode}"
        )

    elif inst_type == "J":
        # J-type: jal rd, imm
        rd, imm = operand
        imm_binary = immediate_to_binary(imm, 21)
        # imm[20] imm[10:1] imm[11] imm[19:12] rd opcode
        machine_code = (
            f"{imm_binary[0]}"
            f"{imm_binary[10:20]}"
            f"{imm_binary[9]}"
            f"{imm_binary[1:9]}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    else:
        raise ValueError(f"Unknown instruction type: {inst_type}")

    return {"Assembly": assembly_instruction, "MachineCode": machine_code, "Type": inst_type}


def strip_comment(line: str) -> str:
    # support '#' and ';' comments
    for sep in ("#", ";"):
        if sep in line:
            line = line.split(sep, 1)[0]
    return line.strip()


def assemble_file(
    in_path: str,
    out_path: Optional[str] = None,
    emit_hex: bool = True,
) -> List[str]:
    """
    Assemble a .s file line by line.
    Returns output lines (also writes to out_path if provided).
    """
    output_lines: List[str] = []
    pc = 0  # each instruction 4 bytes (RV32I)
    with open(in_path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = strip_comment(raw)
            if not line:
                continue
            try:
                res = assemble_to_machine_code(line)
                bin_code = res["MachineCode"]
                if emit_hex:
                    hex_code = bin_to_hex32(bin_code)
                    output_lines.append(f" {hex_code}  ")
                else:
                    output_lines.append(f" {bin_code} ")
                pc += 4
            except Exception as e:
                output_lines.append(f"ERROR line {lineno}: {e}    # {raw.rstrip()}")
                # keep going

    if out_path:
        with open(out_path, "w", encoding="utf-8") as wf:
            wf.write("\n".join(output_lines) + "\n")
    return output_lines


def main():
    parser = argparse.ArgumentParser(description="Simple RV32I assembler (subset) - batch mode")
    parser.add_argument("-f", "--file", help="Input assembly file (.s)")
    parser.add_argument("-o", "--out", help="Output text file (optional)")
    parser.add_argument("--bin", action="store_true", help="Emit binary instead of hex")
    args = parser.parse_args()

    if args.file:
        lines = assemble_file(args.file, out_path=args.out, emit_hex=not args.bin)
        print("\n".join(lines))
    else:
        # fallback: single-line interactive mode (original behavior)
        assembly_instruction = input("Enter assembly instruction: ").strip()
        result = assemble_to_machine_code(assembly_instruction)
        print("Assembly Instruction:", result["Assembly"])
        print("Machine Code:", result["MachineCode"])
        print("Instruction Type:", result["Type"])


if __name__ == "__main__":
    main()
