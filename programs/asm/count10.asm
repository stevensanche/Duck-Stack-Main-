# Lovingly crafted by robots
   LOAD r1,const0_2
  STORE  r1,x_1
loop_3:  #While loop
   LOAD r1,x_1
   LOAD r2,const11_5
   SUB  r1,r1,r2
  SUB  r0,r1,r0 
  JUMP/Z endloop_4
   LOAD r1,x_1
STORE r1,r0,r0[511] # Print
   LOAD r1,x_1
   LOAD r2,const1_6
   ADD  r1,r1,r2
  STORE  r1,x_1
  JUMP loop_3
endloop_4: 
  HALT  r0,r0,r0
x_1: DATA 0 #x
const0_2:  DATA 0
const11_5:  DATA 11
const1_6:  DATA 1
