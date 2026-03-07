import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Générer des données fictives
np.random.seed(42)
n = 100

data = pd.DataFrame({
    'surface_m2': np.random.randint(30, 150, n),
    'nb_chambres': np.random.randint(1, 5, n),
    'age_batiment': np.random.randint(0, 50, n)
})

# Prix = fonction de la surface + bruit
data['prix'] = data['surface_m2'] * 3000 + data['nb_chambres'] * 10000 - data['age_batiment'] * 500 + np.random.normal(0, 15000, n)

print("=== Données immobilières ===")
print(data.head(10))

# Préparer les features et target
X = data[['surface_m2', 'nb_chambres', 'age_batiment']]
y = data['prix']

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraîner le modèle
model = LinearRegression()
model.fit(X_train, y_train)

# Prédictions
y_pred = model.predict(X_test)

# Résultats
print("\n=== Coefficients du modèle ===")
result = pd.DataFrame({
    'Feature': X.columns,
    'Coefficient': model.coef_
})
print(result)

print(f"\nIntercept: {model.intercept_:.2f}")
print(f"R² Score: {r2_score(y_test, y_pred):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.2f} €")

# Exemple de prédiction
output = pd.DataFrame({
    'Surface': [80, 120],
    'Chambres': [2, 4],
    'Age': [10, 5],
    'Prix prédit': model.predict([[80, 2, 10], [120, 4, 5]])
})
print("\n=== Prédictions exemple ===")
print(output)