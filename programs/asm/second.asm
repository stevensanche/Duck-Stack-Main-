#  Second DM2018S:  1 + 2 = 3, but
#  this time reading a value from memory
#  and storing into memory.
#
 ADD   r1,r0,r0[1]    # r1 = 1
 LOAD  r2,x           # r2 = Mem[x]
 ADD   r3,r1,r2       # r3 = r1 + r2
 STORE r3,y           # Mem[y] = r3
 HALT   r0,r0,r0
x: DATA  2              # A memory cell to hold x, initialized to 2
y: DATA 99              # A memory cell to hold y

	
	