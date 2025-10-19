import io
import os
from fastapi.testclient import TestClient

from oncoscan_webapp.backend.main import app

client = TestClient(app)


def test_token_and_me():
    resp = client.post('/token', data={'username': 'doc_user', 'password': 'securepass'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'access_token' in data
    token = data['access_token']

    me = client.get('/users/me', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['user_id'] == 'doc_user'


def test_predict_and_audit(tmp_path):
    # create a small dummy file
    content = b'fake-image-data'
    files = {'file': ('scan.png', io.BytesIO(content), 'image/png')}

    resp = client.post('/token', data={'username': 'doc_user', 'password': 'securepass'})
    token = resp.json()['access_token']

    pr = client.post('/predict', files=files, headers={'Authorization': f'Bearer {token}'})
    assert pr.status_code == 200
    data = pr.json()
    assert data['user_id'] == 'doc_user'
    assert 'audit_id' in data

    # confirm audit_log.csv exists
    audit_csv = os.path.join(os.path.dirname(__file__), '..', 'audit_log.csv')
    assert os.path.exists(audit_csv)
