import pandas as pd
import numpy as np
df = pd.DataFrame({'a': range(100), 'b': np.random.rand(100)})
df.to_csv("/work/outputs/bench_result.csv", index=False)
print("saved")
