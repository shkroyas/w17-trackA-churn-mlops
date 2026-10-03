from churn_mlops.train import train_all
from churn_mlops.registry import promote, challenge
from churn_mlops.drift import monitor

train_all()
promote()
verdict = monitor()
if verdict["drifted"]["significant"]:
    challenge()
