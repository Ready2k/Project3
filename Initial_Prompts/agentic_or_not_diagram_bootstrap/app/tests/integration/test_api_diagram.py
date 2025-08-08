from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

def test_diagram_sequence_endpoint():
    r = client.get('/diagram/demo?view=sequence')
    assert r.status_code == 200
    assert 'mermaid' in r.json()
    assert 'sequenceDiagram' in r.json()['mermaid']

def test_diagram_context_endpoint():
    r = client.get('/diagram/demo?view=context')
    assert r.status_code == 200
    assert 'flowchart' in r.json()['mermaid']

def test_diagram_container_endpoint():
    r = client.get('/diagram/demo?view=container')
    assert r.status_code == 200
    assert 'flowchart' in r.json()['mermaid']
