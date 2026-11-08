import unittest
try:
    from fastapi.testclient import TestClient
    from app.api.main import app
except ImportError:
    TestClient=None

@unittest.skipIf(TestClient is None,'Optional API dependencies are not installed')
class ApiTests(unittest.TestCase):
    def setUp(self):self.client=TestClient(app)
    def test_case_catalogue_is_explicitly_analysis_ineligible(self):
        response=self.client.get('/api/catalog')
        self.assertEqual(response.status_code,200)
        self.assertIs(response.json()['analysis_eligible'],False)
    def test_unknown_plant_is_404(self):
        self.assertEqual(self.client.get('/api/plants/unknown').status_code,404)
    def test_invalid_analysis_dates_rejected(self):
        self.assertEqual(self.client.get('/api/analysis?freeze=9999').status_code,422)
    def test_health_does_not_imply_scientific_validity(self):
        self.assertEqual(self.client.get('/api/health').json()['scientific_validation'],'pending')
