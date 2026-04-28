## 1. Trainer
 
The trainer generates `model.pkl` and `scaler.pkl` used by the API.
 
### Setup
 
```bash
cd machine_learning/trainer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
### Run pipeline
 
```bash
python run_pipeline.py
```

After this completes, `models/model.pkl` and `models/scaler.pkl` will be created. Also mock data will be created.
 
---


## 2. API
 
### Setup
 
```bash
cd machine_learning/api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
> Make sure you have run the trainer's pipeline first, the API requires `model.pkl` and `scaler.pkl` to exist in `trainer/models/`.
 
### Start the server
 
```bash
uvicorn main:app --reload
```