import pandas as pd
df = pd.read_csv("/work/data/population_sample.csv")
print(df.describe())
print("rows:", len(df))
