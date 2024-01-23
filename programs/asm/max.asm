# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.679691 from programs/mal/max.mal
#
   LOAD  r14,r0,r0[510]
   STORE  r14,var_x
   LOAD  r14,r0,r0[510]
   STORE  r14,var_y
    LOAD r14,var_x
    LOAD r13,var_y
   SUB  r0,r14,r13
   JUMP/ZM  else_1  #>
    LOAD r14,var_x
   STORE  r14,r0,r0[511]
	JUMP fi_2
else_1:
    LOAD r14,var_y
   STORE  r14,r0,r0[511]
fi_2:
	HALT  r0,r0,r0
var_x:  DATA 0
var_y:  DATA 0
