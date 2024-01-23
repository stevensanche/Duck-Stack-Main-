# Lovingly crafted by robots
# 2018-05-24 09:28:42.279707 from programs/sum.awl
#
	LOAD r1,const0_2  # Const 0
	STORE  r1,sum_1
	LOAD r1,r0,r0[510]
	STORE  r1,x_3
loop_4:  #While loop
	LOAD r2,x_3
	SUB  r0,r2,r0 
	JUMP/Z endloop_5
	LOAD r1,sum_1
	LOAD r2,x_3
	ADD  r1,r1,r2
	STORE  r1,sum_1
	LOAD r1,r0,r0[510]
	STORE  r1,x_3
	JUMP loop_4
endloop_5: 
	LOAD r1,sum_1
	STORE  r1,r0,r0[511]
	HALT  r0,r0,r0
sum_1: DATA 0 #sum
x_3: DATA 0 #x
const0_2:  DATA 0
