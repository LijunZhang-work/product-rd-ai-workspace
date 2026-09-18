import json
from hpt.cli import main
from hpt.examples import save_example


def test_init_validate_and_schema(tmp_path,capsys):
    folder=tmp_path/'case'
    assert main(['init-demo',str(folder)])==0
    assert main(['validate',str(folder),'--output',str(tmp_path/'runs')])==0
    assert main(['schema',str(tmp_path/'schemas')])==0
    assert json.loads((tmp_path/'schemas'/'route.schema.json').read_text())['additionalProperties'] is False


def test_cli_rejection_keeps_artifact(tmp_path,capsys):
    folder=save_example(tmp_path/'case')
    route=json.loads((folder/'route.json').read_text())
    route['steps'][1]['force']=True
    (folder/'route.json').write_text(json.dumps(route))
    assert main(['validate',str(folder),'--output',str(tmp_path/'runs')])==2
    evidence=list((tmp_path/'runs').glob('*/rejection.json'))
    assert len(evidence)==1
    assert 'force' in evidence[0].read_text()

