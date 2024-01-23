# Lovingly crafted by the robots of CIS 211
# 2022-05-08 21:18:10.500629 from programs/mal/absdiff.mal
#
   LOAD  r14,r0,r0[510]
   STORE  r14,var_x
   LOAD  r14,r0,r0[510]
   STORE  r14,var_y
    LOAD r14,var_x
    LOAD r13,var_y
   SUB  r14,r14,r13
    SUB  r0,r14,r0  # <Abs>
    JUMP/PZ stay_positive_1
    SUB r14,r0,r14  # Flip the sign
stay_positive_1:   # </Abs>
   STORE  r14,var_absdiff
    LOAD r14,var_absdiff
	SUB  r14,r0,r14  # Flip the sign
   STORE  r14,var_neg
    LOAD r14,var_absdiff
   STORE  r14,r0,r0[511]
    LOAD r14,var_neg
   STORE  r14,r0,r0[511]
	HALT  r0,r0,r0
var_x:  DATA 0
var_y:  DATA 0
var_absdiff:  DATA 0
var_neg:  DATA 0
