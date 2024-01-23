# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.596602 from programs/mal/fact.mal
#
   LOAD  r14,r0,r0[510]
   STORE  r14,var_x
    LOAD r14,const_1
   STORE  r14,var_fact
while_do_1:
    LOAD r14,var_x
    LOAD r13,const_1
   SUB  r0,r14,r13
   JUMP/ZM  od_2  #>
    LOAD r14,var_fact
    LOAD r13,var_x
   MUL  r14,r14,r13
   STORE  r14,var_fact
    LOAD r14,var_x
    LOAD r13,const_1
   SUB  r14,r14,r13
   STORE  r14,var_x
   JUMP  while_do_1
od_2:
    LOAD r14,var_fact
   STORE  r14,r0,r0[511]
	HALT  r0,r0,r0
const_1:  DATA 1
var_x:  DATA 0
var_fact:  DATA 0
