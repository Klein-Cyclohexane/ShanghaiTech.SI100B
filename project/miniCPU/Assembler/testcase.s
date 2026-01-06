addi x1, x0, 10
addi x2, x0, -20
addi x3, x0, 5
add x4 x1, x2
add x5, x1, x3
sub x6 x1, x2
sub x7, x1, x3
and x8, x1, x2
and x9, x1, x3
or x10, x1, x2
or x11, x1, x3
slt x12, x1, x2
slt x13, x2, x1
slti x14, x1, -8 
slti, x15, x1, 28
addi x16, x16, 1
addi x17, x0, 3
bne x16, x17, -8
jal x16, 8
addi x17, x0, 7
andi x19, x1, 8
andi x20, x2, 18
ori x21, x1, 8
ori x22, x2, 18
sw x19, 0(x5)
sw x19, 4(x5)
lw x18, 0(x5)



