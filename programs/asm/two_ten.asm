#
# Mystery function ... what does this print?
#
	ADD   r1,r0,r0[1]  # r1 = 1
	LOAD  r12,mmap_in  # r12 = @input
	LOAD  r2,r12,r0    # r2 = input()
	SUB  r2,r2,r0	   # if r2 == 0:
	JUMP/Z   done      #     break
again:		   	   # while r2 != 0 do
	ADD  r1,r1,r1	   #    r1 = r1 + r1
	SUB  r2,r2,r0[1]   #    r2 = r2 - 1
	JUMP/P  again      # od
done:   LOAD  r12,mmap_out # @output
	STORE r1,r12,r0    # print r1
	HALT  r0,r0,r0	   # end
mmap_in:      DATA 510
mmap_out:     DATA 511

	
