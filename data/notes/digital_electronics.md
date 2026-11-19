# Digital Electronics

## Logic gates
NAND and NOR are universal gates because any Boolean function can be built using only one of them. XOR outputs 1 when its inputs differ. De Morgan's theorems state that the complement of an AND equals the OR of the complements, and the complement of an OR equals the AND of the complements.

## Flip-flops
An SR flip-flop has an invalid state when both S and R are 1. The JK flip-flop removes this problem; when J and K are both 1 it toggles its output. A D flip-flop copies its D input to the output on the active clock edge, so it is used to store one bit in registers. A T flip-flop toggles on each clock pulse when T is 1 and is used in counters.

## Combinational circuits
A multiplexer selects one of many inputs using select lines. A 4-to-1 multiplexer needs 2 select lines. A decoder converts an n-bit input into one of 2^n outputs. A half adder adds two bits and produces a sum and a carry, where the sum is XOR and the carry is AND. A full adder also accepts a carry-in.

## Sequential circuits
A synchronous counter clocks all flip-flops at the same time, so it avoids the cumulative propagation delay of an asynchronous ripple counter. A mod-N counter counts through N states. A shift register moves its stored bits along by one position on each clock pulse.

## Number systems
Two's complement represents negative numbers by inverting all the bits and adding 1. An n-bit two's complement number ranges from -2^(n-1) to 2^(n-1)-1. Gray code changes only one bit between consecutive values, which reduces errors in position encoders.
