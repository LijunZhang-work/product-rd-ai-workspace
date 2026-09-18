import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from hpt.examples import make_case
from hpt.fixture import serve_fixture
from hpt.explorer import explore, OutcomeSpec, prepare_case
from hpt.evidence import verify_integrity
from hpt.contracts import PolicyError


class ProtocolExplorer:
    """Transport stub: never described as a real visual model."""
    config=SimpleNamespace(supports_images=True)
    def __init__(self,stale=False):
        self.calls=[];self.stale=stale;self.last_receipt={}
    def complete_json(self,prompt,image):
        import re
        from hpt.evidence import digest_file
        assert image.is_file()
        observation=int(re.findall(r'\nObservation ID: (\d+)',prompt)[-1])
        self.calls.append(str(image))
        self.last_receipt={'model':'protocol-stub-not-visual-AI','image_sha256':digest_file(image),'image_sent':True}
        return {'observation_id':observation-1 if self.stale else observation,'done':True,'business_id':'protocol','explanation':'Protocol-only stop, not a real completed business workflow'}


@pytest.mark.browser
def test_explorer_stale_observation_is_rejected(tmp_path):
    with serve_fixture() as (_,url):
        r,_,env,inputs=make_case(base_url=url)
        client=ProtocolExplorer(stale=True)
        folder,status=explore('Protocol test',env,{k:v.model_dump() for k,v in r.parameters.items()},inputs,client,tmp_path)
        assert status=='failed'
        assert 'stale' in json.loads((folder/'exploration.json').read_text())['error']
        assert verify_integrity(folder)==[]


@pytest.mark.browser
def test_done_is_only_candidate_and_cannot_remove_need_for_outcomes(tmp_path):
    with serve_fixture() as (_,url):
        r,_,env,inputs=make_case(base_url=url)
        folder,status=explore('Protocol test',env,{k:v.model_dump() for k,v in r.parameters.items()},inputs,ProtocolExplorer(),tmp_path/'explore')
        assert status=='candidate'
        assert not (folder/'result.json').exists()
        outcome=OutcomeSpec(case_id='example',original_intent='Protocol test',oracle_status='pending',checkpoints={})
        with pytest.raises(PolicyError):
            prepare_case(folder,outcome,tmp_path/'prepared')


def test_nonvisual_explorer_refused_before_browser(tmp_path):
    model=SimpleNamespace(config=SimpleNamespace(supports_images=False))
    r,_,env,inputs=make_case()
    with pytest.raises(PolicyError):
        explore('Task',env,{k:v.model_dump() for k,v in r.parameters.items()},inputs,model,tmp_path)

