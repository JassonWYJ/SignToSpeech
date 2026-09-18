import joblib
import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import GroupKFold
from sklearn.svm import SVC

from train_rbf_svm_raw import load_dataset, DEFAULT_DATA_DIR

MODEL_PATH = "rbf_svm_1m_raw.joblib"

X, y, groups, _ = load_dataset(DEFAULT_DATA_DIR)
final_model = joblib.load(MODEL_PATH)

cv = GroupKFold(n_splits=5)
oof_prediction = np.empty(len(y), dtype=object)

for train_index, test_index in cv.split(X, y, groups):
    fold_model = SVC(
        kernel="rbf",
        C=final_model.C,
        gamma=final_model.gamma,
        class_weight=final_model.class_weight,
    )

    fold_model.fit(X[train_index], y[train_index])
    oof_prediction[test_index] = fold_model.predict(X[test_index])

class_names = final_model.classes_

# 数量矩阵
cm_count = confusion_matrix(
    y,
    oof_prediction,
    labels=class_names,
)

# 按真实类别归一化
cm_rate = confusion_matrix(
    y,
    oof_prediction,
    labels=class_names,
    normalize="true",
)

fig, axes = plt.subplots(1, 2, figsize=(20, 9))

ConfusionMatrixDisplay(
    cm_count,
    display_labels=class_names,
).plot(
    ax=axes[0],
    cmap="Blues",
    values_format="d",
    xticks_rotation=45,
)
axes[0].set_title("Out-of-fold confusion counts")

ConfusionMatrixDisplay(
    cm_rate,
    display_labels=class_names,
).plot(
    ax=axes[1],
    cmap="YlGn",
    values_format=".0%",
    xticks_rotation=45,
)
axes[1].set_title("Out-of-fold confusion rates")

plt.tight_layout()
plt.savefig("cv_confusion_heatmap.png", dpi=200)
plt.show()

print("Per-sign recall:")
for sign, recall in zip(class_names, np.diag(cm_rate)):
    print(f"{sign:12s}: {recall:.2%}")