# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.566447 from programs/mal/countdown.mal
#
    LOAD r14,const_10
   STORE  r14,var_x
while_do_1:
    LOAD r14,var_x
    LOAD r13,const_0
   SUB  r0,r14,r13
   JUMP/M  od_2  #>=
    LOAD r14,var_x
   STORE  r14,r0,r0[511]
    LOAD r14,var_x
    LOAD r13,const_1
   SUB  r14,r14,r13
   STORE  r14,var_x
   JUMP  while_do_1
od_2:
	HALT  r0,r0,r0
const_0:  DATA 0
const_1:  DATA 1
const_10:  DATA 10
var_x:  DATA 0
