from sage.all import *
from math import gcd
from Crypto.Util.number import bytes_to_long, isPrime
from secret import left_prime, right_prime, x1, y1, x2, y2, hmw_k, flag

N = left_prime * right_prime
M = (bytes_to_long(flag) + (x1 + y1 + x2 + y2)) % N
C = pow(M, hmw_k, N)
F = RealField(0x539)
vx = vector(F, [x1, x2])
vy = vector(F, [y1, y2])
theta = F.random_element(min=-pi, max=pi)
a = cos(theta)
b = sin(theta)
R = matrix(F, [[a - b, - (a + b)], [a + b, a - b]])
vx = R * vx
vy = R * vy
print(f"{N = }")
print(f"{C = }")
print(f"{vx = }")
print(f"{vy = }")