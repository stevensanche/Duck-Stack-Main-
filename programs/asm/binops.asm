# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.536575 from programs/mal/binops.mal
#
    LOAD r14,const_7
   STORE  r14,var_x
    LOAD r14,var_x
    LOAD r13,const_7
   ADD  r14,r14,r13
   STORE  r14,var_y
    LOAD r14,var_x
    LOAD r13,var_y
   MUL  r14,r14,r13
   STORE  r14,var_z
    LOAD r14,var_x
    LOAD r13,var_y
    LOAD r12,var_z
   DIV  r13,r13,r12
   SUB  r14,r14,r13
   STORE  r14,var_q
	HALT  r0,r0,r0
const_7:  DATA 7
var_x:  DATA 0
var_y:  DATA 0
var_z:  DATA 0
var_q:  DATA 0
