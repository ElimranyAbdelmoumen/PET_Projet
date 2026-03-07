import pandas as pd
import numpy as np

# Créer un DataFrame d'exemple
df = pd.DataFrame({
    'nom': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'age': [25, 30, 35, 28, 22],
    'salaire': [45000, 55000, 65000, 50000, 40000],
    'score': np.random.randint(50, 100, 5)
})

print("=== DataFrame original ===")
print(df)

print("\n=== Statistiques ===")
result = df.describe()
print(result)

print("\n=== Moyenne des salaires ===")
print(f"Moyenne: {df['salaire'].mean():.2f} €")

print("\n=== Filtrage: age > 25 ===")
output = df[df['age'] > 25]
print(output)