# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.768915 from programs/mal/read_add_print.mal
#
   LOAD  r14,r0,r0[510]
   STORE  r14,var_x
   LOAD  r14,r0,r0[510]
   STORE  r14,var_y
    LOAD r14,var_x
    LOAD r13,var_y
   ADD  r14,r14,r13
   STORE  r14,r0,r0[511]
	HALT  r0,r0,r0
var_x:  DATA 0
var_y:  DATA 0
