import argparse
from typing import List, Tuple, Optional

import instructions


def preprocess_instruction(line: str) -> Tuple[str, List[str]]:#处理汇编文件的每一行
    parts = line.replace(",", "").replace("(", " ").replace(")", "").split()
    if not parts:
        raise ValueError("Empty instruction")
    mnemonic = parts[0]
    operands = parts[1:]
    return mnemonic, operands


def register_to_binary(register: str) -> str:#寄存器转换为二进制编码
    if register.startswith("x"):
        reg_str = register[1:]
    try:
        reg_num = int(reg_str)
    except Exception:
        raise ValueError(f"Invalid register name: {register}")
    if not (0 <= reg_num <= 31):
        raise ValueError(f"Register out of range x0-x31: {register}")
    return format(reg_num, "05b")


def immediate_to_binary(immediate: str, bits: int) -> str:
    if immediate.startswith("x"):
        immediate = immediate[1:]
    try:
        imm = int(immediate, 0)
    except ValueError:
        raise ValueError(f"Invalid immediate: {immediate}")
    if imm < 0:
        imm = (1 << bits) + imm   #负数补码转换
    return format(imm & ((1 << bits) - 1), f"0{bits}b")


def bin_to_hex32(bin_str: str) -> str:#输出二进制转十六进制
    if len(bin_str) != 32:
        raise ValueError(f"Expected 32-bit machine code, got {len(bin_str)} bits")
    return format(int(bin_str, 2), "08x")


def assemble_to_machine_code(assembly_instruction: str) -> dict:
    mnemonic, operand = preprocess_instruction(assembly_instruction)
    mnemonic = mnemonic.lower().strip()
    inst = instructions.INSTRUCTIONS_SET.get(mnemonic)
    if inst is None:
        raise ValueError(f"Unknown mnemonic: {mnemonic}")

    opcode = inst["opcode"]
    inst_type = inst["type"]  #完成从instructions的嵌套字典中获取信息

    if inst_type == "R":
        if len(operand) != 3:
            raise ValueError(f"R-type needs 3 operands, got {len(operand)}: {assembly_instruction}")
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
        if len(operand) != 3:
            raise ValueError(f"I1-type needs 3 operands, got {len(operand)}: {assembly_instruction}")
        load_inst = ["lw", "lb", "lh", "lbu", "lhu"]
        if mnemonic in load_inst:
            rd, imm, rs1 = operand
        else:
            rd, rs1, imm = operand
        try:
            imm_val = int(imm, 0)
        except ValueError:
            raise ValueError(f"Invalid immediate for I1-type: {imm}")
        if not (-2**11 <= imm_val <= 2**11 - 1):
            raise ValueError(f"I1-type immediate out of range (-2048~2047): {imm}")
        imm_binary = immediate_to_binary(imm, 12)
        machine_code = (
            f"{imm_binary}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    elif inst_type == "I2":
        if len(operand) != 3:
            raise ValueError(f"I2-type needs 3 operands, got {len(operand)}: {assembly_instruction}")
        rd, rs1, imm = operand
        try:
            imm_val = int(imm, 0)
        except ValueError:
            raise ValueError(f"Invalid immediate for I2-type: {imm}")
        if not (0 <= imm_val <= 31):
            raise ValueError(f"I2-type immediate out of range (0~31): {imm}")
        imm_binary = immediate_to_binary(imm, 5)
        machine_code = (
            f"{inst['funct7']}"
            f"{imm_binary}"
            f"{register_to_binary(rs1)}"
            f"{inst['funct3']}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    elif inst_type == "S":
        if len(operand) != 3:
            raise ValueError(f"S-type needs 3 operands, got {len(operand)}: {assembly_instruction}")
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
        if len(operand) != 3:
            raise ValueError(f"B-type needs 3 operands, got {len(operand)}: {assembly_instruction}")
        rs1, rs2, imm = operand
        imm_binary = immediate_to_binary(imm, 13)
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
        if len(operand) != 2:
            raise ValueError(f"J-type needs 2 operands, got {len(operand)}: {assembly_instruction}")
        rd, imm = operand
        imm_binary = immediate_to_binary(imm, 21)
        machine_code = (
            f"{imm_binary[0]}"
            f"{imm_binary[10:20]}"
            f"{imm_binary[9]}"
            f"{imm_binary[1:9]}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    elif inst_type == "U":
        if len(operand) != 2:
            raise ValueError(f"U-type needs 2 operands, got {len(operand)}: {assembly_instruction}")
        rd, imm = operand
        try:
            imm_val = int(imm, 0)
        except ValueError:
            raise ValueError(f"Invalid immediate for U-type: {imm}")
        if not (0 <= imm_val <= 2**20 - 1):
            raise ValueError(f"U-type immediate out of range (0~1048575): {imm}")
        imm_binary = immediate_to_binary(imm, 20)
        machine_code = (
            f"{imm_binary}"
            f"{register_to_binary(rd)}"
            f"{opcode}"
        )

    else:
        raise ValueError(f"Unknown instruction type: {inst_type}")

    return {"Assembly": assembly_instruction, "MachineCode": machine_code, "Type": inst_type} #完成机器码的转换


def strip_comment(line: str) -> str:  # 支持#注释
    for sep in ("#", ";"):
        if sep in line:
            line = line.split(sep, 1)[0]
    return line.strip()


def assemble_file(
    in_path: str,     #文件地址
    emit_hex: bool = True,  #控制输出二进制或16进制
) -> List[str]:
    output_lines: List[str] = []
    pc = 0
    with open(in_path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):     #enumerate给予序号，raw是行内容，lineno是行序号
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
                output_lines.append(f"ERROR line {lineno}: {e}    # {raw.rstrip()}")   #返回原始s文件捕获异常
    return output_lines

def main():
    parser = argparse.ArgumentParser(description="Simple RV32I assembler (full set) - batch mode")
    parser.add_argument("-f", "--file", help="Input assembly file (.s)", required=True)
    parser.add_argument("-o", "--out", help="Output text file (optional)")
    parser.add_argument("--bin", action="store_true", help="Emit binary instead of hex")
    args = parser.parse_args()

    lines = assemble_file(args.file, emit_hex=not args.bin)
    print("\n".join(lines))


if __name__ == "__main__":
    main()