import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

clf_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

clf_pipeline.fit(X_train_final, y_train)
y_pred = clf_pipeline.predict(X_test_final)

print("Classification Report for the Reworked Model:")
print(classification_report(y_test, y_pred))

# Save the logic to CSV for user inspection
df_cleaned.to_csv('reworked_mock_data.csv', index=False)