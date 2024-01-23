# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.624635 from programs/mal/fives.mal
#
    LOAD r14,const_100
   STORE  r14,var_x
while_do_1:
    LOAD r14,var_x
    LOAD r13,const_0
   SUB  r0,r14,r13
   JUMP/ZM  od_2  #>
    LOAD r14,var_x
    LOAD r13,const_5
    LOAD r12,var_x
    LOAD r11,const_5
   DIV  r12,r12,r11
   MUL  r13,r13,r12
   SUB  r14,r14,r13
   STORE  r14,var_remainder
    LOAD r14,var_remainder
    LOAD r13,const_0
   SUB  r0,r14,r13
   JUMP/PM  else_3  #==
    LOAD r14,var_x
   STORE  r14,r0,r0[511]
	JUMP fi_4
else_3:
fi_4:
    LOAD r14,var_x
    LOAD r13,const_1
   SUB  r14,r14,r13
   STORE  r14,var_x
   JUMP  while_do_1
od_2:
	HALT  r0,r0,r0
const_0:  DATA 0
const_1:  DATA 1
const_5:  DATA 5
const_100:  DATA 100
var_x:  DATA 0
var_remainder:  DATA 0
