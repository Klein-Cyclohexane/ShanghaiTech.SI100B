addi x1, x0, 5  #initializes x1 as 5
addi x2, x0, -2 #initializes x2 as -2  
add x0, x1, x2 # test if x0 = 0
addi x3, x0, -5 #initializes x3 as -5
addi x4, x0, 3  #initializes x4 as 3
addi x5, x0, 0xA #initializes x5 as 10
addi x16, x1, 0 # x16 = 5
add x6, x1, x4  # x6 = 8
sub x7, x1, x4  # x7 = 2
sll x8, x1, x4  # x8 = 0x28
srl x9, x5, x4  # x9 = 1
sra x10, x2, x4 # x10 = -1
slt x11, x2, x1 # x11 = 1
sltu x12, x2, x1 # x12 = 0
xor x13, x1, x4 # x13 = 6
and x14, x1, x4 # x14 = 1
or x15, x1, x4  # x15 = 7
slti x16, x1, -2 # x16 = 0
sltiu x17, x1, 10 # x17 = 1
xori x18, x5, 5 # x18 = 15
ori x19, x0, 7 # x19 = 7
ori x31, x1, 2047   # x31 = 0x000007FF
andi x20, x5, 3 # x20 = 2
slli x21, x1, 2 # x21 = 0x14
srli x22, x5, 2 # x22 = 2
srai x23, x3, 2 # x23 = -2
lui  x29, 0x123 # x29 = 0x00012300
addi x4, x4, 1  #bne loop, x4 = 5 when the loop is over
bne x4, x1, -4 
jal x30, 8  
addi x1, x0, 7  # if jal fail, x1 = 7
auipc x31, 1   # x31 = pc = 0x10A8
slli x1, x2, 32     # Imm out of range(5)
add x1, x2          # Missing operand
add x32, x1, x2     # Register out of range
addi x1, x2, 2048   # Imm out of range(12)
lw x1, abc(x2)      # Imm format error
sw x1, x2, 10       # operand order error
lui x1, 0x100000    # Imm out of range(20)