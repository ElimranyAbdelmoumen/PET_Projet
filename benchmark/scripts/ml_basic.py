import numpy as np
from sklearn.linear_model import LinearRegression
X = np.random.rand(500, 5)
y = np.random.rand(500)
model = LinearRegression().fit(X, y)
print("score:", model.score(X, y))
