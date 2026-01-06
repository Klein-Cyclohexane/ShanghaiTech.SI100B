import os
import math
import argparse
import numpy as np

class Memory:
    addr_bits: int
    data_bits: int
    mem: np.ndarray
    endian: str

    def __init__(self, addr_bits: int = 8, data_bits: int = 8, endian: str = "little"):
        self.addr_bits = addr_bits
        self.data_bits = data_bits
        self.endian = endian  # "little" 或 "big"
        
        self.mem = np.zeros((2**addr_bits,), dtype=np.uint32 if data_bits <= 32 else np.uint64)

    def load_from_memory(self, mem_img_path: str):
        if not os.path.exists(mem_img_path):
            raise FileNotFoundError(f"Memory image file {mem_img_path} does not exist.")

        with open(mem_img_path, "r") as f:
            mem_img_raw = f.readlines()
        
        memory_size = len(mem_img_raw) - 1

        assert memory_size * 16 == 2**self.addr_bits, f"Memory size {memory_size} does not match address bits {self.addr_bits}."

        mem_image = np.zeros((2**self.addr_bits,), dtype=np.uint32 if self.data_bits <= 32 else np.uint64)
        addr = 0
        for i, line in enumerate(mem_img_raw):
            if i == 0:
                continue
            
            raw = line.strip().split(":")
            start_addr, datas = raw[0], raw[1].split()
            
            start_addr = int(start_addr, 16)
            if (addr != start_addr):
                raise ValueError(f"Address mismatch: expected {addr}, got {start_addr}.")
            
            for data_str in datas:
                data_raw = int(data_str, 16)
                if (data_raw < 0) or (data_raw >= 2**self.data_bits):
                    raise ValueError(f"Data out of range: {data_raw}.")
                data = data_raw
                mem_image[addr] = data
                addr += 1

        self.mem = mem_image
    
    def load_from_binary_instructions(self, instruction_file: str):
        """
        从二进制指令文件加载数据。
        文件格式：每行一个32位十六进制指令，后面可以跟 # 注释
        
        指令会根据data_bits自动拆分：
        - data_bits=32: 一条指令占用1个内存单元
        - data_bits=8:  一条指令拆分成4个字节，占用4个内存单元
        - data_bits=16: 一条指令拆分成2个半字，占用2个内存单元
        
        支持大端序和小端序。
        
        例如：
        ```python
        00ab3471 # 这是一条指令
        ```
        """
        if not os.path.exists(instruction_file):
            raise FileNotFoundError(f"Instruction file {instruction_file} does not exist.")
        
        with open(instruction_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 读取所有32位指令
        instructions = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "#" in line:
                instruction_part = line.split("#")[0].strip()
            else:
                instruction_part = line
            
            if not instruction_part:
                continue
            
            try:
                instruction_value = int(instruction_part, 16)
                instructions.append(instruction_value)
            except ValueError as e:
                raise ValueError(f"Line {line_num}: Invalid hex value '{instruction_part}': {e}")
        
        bytes_per_instruction = 4
        bytes_per_memory_unit = self.data_bits // 8
        
        if bytes_per_memory_unit == 0 or self.data_bits % 8 != 0:
            raise ValueError(f"data_bits must be a multiple of 8, got {self.data_bits}")
        
        memory_units_per_instruction = bytes_per_instruction // bytes_per_memory_unit
        if bytes_per_instruction % bytes_per_memory_unit != 0:
            raise ValueError(f"Instruction size (32 bits) must be divisible by data_bits ({self.data_bits})")
        
        total_memory_units_needed = len(instructions) * memory_units_per_instruction
        max_memory_size = 2**self.addr_bits
        
        if total_memory_units_needed > max_memory_size:
            raise ValueError(
                f"Too many instructions: {len(instructions)} instructions need "
                f"{total_memory_units_needed} memory units, but only {max_memory_size} available."
            )
        
        self.mem = np.zeros((max_memory_size,), dtype=np.uint32 if self.data_bits <= 32 else np.uint64)
        
        mem_addr = 0
        for instruction in instructions:
            if self.data_bits == 32:
                self.mem[mem_addr] = instruction
                mem_addr += 1
            elif self.data_bits == 8:
                if self.endian == "little":
                    self.mem[mem_addr] = instruction & 0xFF
                    self.mem[mem_addr + 1] = (instruction >> 8) & 0xFF
                    self.mem[mem_addr + 2] = (instruction >> 16) & 0xFF
                    self.mem[mem_addr + 3] = (instruction >> 24) & 0xFF
                else:
                    self.mem[mem_addr] = (instruction >> 24) & 0xFF
                    self.mem[mem_addr + 1] = (instruction >> 16) & 0xFF
                    self.mem[mem_addr + 2] = (instruction >> 8) & 0xFF
                    self.mem[mem_addr + 3] = instruction & 0xFF
                mem_addr += 4
            elif self.data_bits == 16:
                if self.endian == "little":
                    self.mem[mem_addr] = instruction & 0xFFFF
                    self.mem[mem_addr + 1] = (instruction >> 16) & 0xFFFF
                else:
                    self.mem[mem_addr] = (instruction >> 16) & 0xFFFF
                    self.mem[mem_addr + 1] = instruction & 0xFFFF
                mem_addr += 2
            else:
                raise ValueError(f"Unsupported data_bits: {self.data_bits}. Supported values: 8, 16, 32")

    def print_memory(self):
        addr_hex_width = (self.addr_bits + 3) // 4
        endian_str = "小端序" if self.endian == "little" else "大端序"
        print("=" * 50)
        print(f"内存配置: {self.addr_bits}位地址, {self.data_bits}位数据, {endian_str}")
        print(f"地址宽度: {addr_hex_width} 个十六进制位, 数据宽度: {self.data_bits//4} 个十六进制位")
        print("=" * 50)
        for i in range(0, 2**self.addr_bits, 16):
            addr = i
            print(f"{addr:0{addr_hex_width}x}: ", end="")
            for j in range(16):
                data = self.mem[i + j]
                print(f"{data:0{self.data_bits//4}x}", end=" ")
            print("")
    
    def write_to_memory(self, mem_img_path: str):
        addr_hex_width = (self.addr_bits + 3) // 4
        endian_str = "小端序" if self.endian == "little" else "大端序"
        
        dir_path = os.path.dirname(mem_img_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(mem_img_path, "w") as f:
            f.write("v3.0 hex words addressed\n")
            for i in range(0, 2**self.addr_bits, 16):
                addr = i
                f.write(f"{addr:0{addr_hex_width}x}: ")
                for j in range(16):
                    data = self.mem[i + j]
                    f.write(f"{data:0{self.data_bits//4}x} ")
                f.write("\n")
        
        print(f"\n" + "="*50)
        print(f"内存配置: {self.addr_bits}位地址, {self.data_bits}位数据, {endian_str}")
        print(f"地址宽度: {addr_hex_width} 个十六进制位, 数据宽度: {self.data_bits//4} 个十六进制位")
        print(f"Memory 文件已保存到: {mem_img_path}")
        print("="*50)

def main():
    """主函数：解析命令行参数并执行转换"""
    parser = argparse.ArgumentParser(
        description="将二进制指令文件转换为Memory格式文件",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="Instruction.bin",
        help="输入的二进制指令文件路径"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output/Memory.txt",
        help="输出的 Memory 文件路径"
    )
    
    parser.add_argument(
        "-a", "--addr-bits",
        type=int,
        default=16,
        help="地址位宽"
    )
    
    parser.add_argument(
        "-d", "--data-bits",
        type=int,
        default=32,
        help="数据位宽"
    )
    
    parser.add_argument(
        "-e", "--endian",
        type=str,
        choices=["little", "big"],
        default="little",
        help="字节序：little (小端序，默认) 或 big (大端序)"
    )
    
    parser.add_argument(
        "--print-memory",
        action="store_true",
        help="在终端打印内存内容"
    )
    
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="创建示例指令文件"
    )
    
    args = parser.parse_args()
    
    if args.create_example:
        example_file = "Example_Instructions.bin"
        with open(example_file, "w", encoding="utf-8") as f:
            f.write("# 示例指令文件\n")
            f.write("# 格式：十六进制数 # 注释\n")
            f.write("\n")
            f.write("00ab3471 # 加载指令\n")
            f.write("12345678 # 算术运算\n")
            f.write("abcdef00 # 跳转指令\n")
            f.write("# 这是注释行，会被忽略\n")
            f.write("ffffffff # 最大值\n")
            f.write("00000000 # NOP\n")
        print(f"已创建示例指令文件: {example_file}")
        return
    
    if not os.path.exists(args.input):
        print(f"错误：输入文件 '{args.input}' 不存在！")
        print(f"提示：使用 --create-example 创建示例文件")
        return
    
    memory = Memory(args.addr_bits, args.data_bits, args.endian)
    
    memory.load_from_binary_instructions(args.input)
    
    if args.print_memory:
        print("")
        memory.print_memory()
    
    memory.write_to_memory(args.output)


if __name__ == "__main__":
    main()
