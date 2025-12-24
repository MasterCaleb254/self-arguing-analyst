# 1. Generate synthetic dataset for testing
python -c "
from src.synthetic.generator import SyntheticIncidentGenerator
gen = SyntheticIncidentGenerator()
incidents = gen.generate_dataset(size=100)
gen.save_dataset(incidents, 'data/synthetic/test_dataset.jsonl')
print('Generated 100 synthetic incidents')
"

# 2. Run evaluation
python evaluate_system.py --generate 50 --output results/evaluation

# 3. Start the API
uvicorn api.main:app --reload

# 4. Test the API
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_text": "User downloaded suspicious executable from unknown domain. File attempted to modify registry keys.",
    "enable_mitre": true,
    "priority": "high"
  }'