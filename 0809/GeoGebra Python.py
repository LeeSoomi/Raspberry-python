# !pip install sympy matplotlib numpy
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

# 심볼 정의
x = sp.symbols('x')

# 함수 정의
expr = sp.sin(x)

# 함수의 시각화
sp.plot(expr, (x, -10, 10))




