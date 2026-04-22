import pandas as pd
import numpy as np
df = pd.DataFrame({'x': range(1000), 'y': np.random.rand(1000)})
result = df.describe()
print(result)
