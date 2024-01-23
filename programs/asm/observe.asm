# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.707142 from programs/mal/observe.mal
#
   LOAD  r14,r0,r0[510]
   STORE  r14,var_watch
    LOAD r14,const_0
   STORE  r14,var_count
   LOAD  r14,r0,r0[510]
   STORE  r14,var_observe
while_do_1:
    LOAD r14,var_observe
    LOAD r13,const_0
   SUB  r0,r14,r13
   JUMP/Z  od_2  #!=
    LOAD r14,var_watch
    LOAD r13,var_observe
   SUB  r0,r14,r13
   JUMP/PM  else_3  #==
    LOAD r14,var_count
    LOAD r13,const_1
   ADD  r14,r14,r13
   STORE  r14,var_count
	JUMP fi_4
else_3:
fi_4:
   LOAD  r14,r0,r0[510]
   STORE  r14,var_observe
   JUMP  while_do_1
od_2:
    LOAD r14,var_count
   STORE  r14,r0,r0[511]
	HALT  r0,r0,r0
const_0:  DATA 0
const_1:  DATA 1
var_watch:  DATA 0
var_count:  DATA 0
var_observe:  DATA 0
