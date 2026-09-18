import base64
import json
import threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import pytest

from hpt.models import ModelClient, ModelConfig
from hpt.evidence import digest_file
from hpt.examples import make_case
from hpt.explorer import compile_candidate
from hpt.contracts import PolicyError


@contextmanager
def protocol_server(answer):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(payload)
            body = json.dumps({"id": "protocol-test", "model": "fake-test-service-not-a-real-model", "choices": [{"message": {"content": json.dumps(answer)}}], "usage": {"total_tokens": 0}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/chat/completions', requests
    finally:
        server.shutdown();server.server_close();thread.join()


def test_model_transport_really_sends_image_bytes(tmp_path):
    image = tmp_path/'image.png'
    image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jZ1kAAAAASUVORK5CYII='))
    with protocol_server({"ok":True}) as (url,requests):
        client=ModelClient(ModelConfig(endpoint=url,model='protocol',supports_images=True))
        assert client.complete_json('Protocol only',image)=={"ok":True}
        item=requests[0]['messages'][1]['content'][1]['image_url']['url']
        assert base64.b64decode(item.split(',')[1])==image.read_bytes()
        assert client.last_receipt['image_sha256']==digest_file(image)
        assert client.last_receipt['image_sent'] is True


def test_text_model_cannot_claim_image_input(tmp_path):
    image=tmp_path/'image.png';image.write_bytes(b'not-used')
    with protocol_server({}) as (url,requests):
        client=ModelClient(ModelConfig(endpoint=url,model='text-only'))
        with pytest.raises(ValueError,match='does not support images'):
            client.complete_json('Look',image)
        assert requests==[]


def test_text_compiler_preserves_business_contract(tmp_path):
    route,behavior,_,inputs=make_case()
    answer=route.model_dump();answer['revision']=2;answer['summary']='A clearer description'
    with protocol_server(answer) as (url,requests):
        client=ModelClient(ModelConfig(endpoint=url,model='protocol-text'))
        compiled=compile_candidate(route,behavior,inputs,client,tmp_path/'candidate.json')
        assert compiled.revision==2
        assert all(x['type']=='text' for x in requests[0]['messages'][1]['content'])


def test_text_compiler_rejects_changed_expectations(tmp_path):
    route,behavior,_,inputs=make_case()
    answer=route.model_dump()
    answer['checkpoints']['CP_PERSISTED']['assertions']=[{'target':'heading','kind':'visible'}]
    with protocol_server(answer) as (url,_):
        client=ModelClient(ModelConfig(endpoint=url,model='protocol-text'))
        with pytest.raises(PolicyError):
            compile_candidate(route,behavior,inputs,client,tmp_path/'bad.json')
    assert not (tmp_path/'bad.json').exists()


def test_model_config_rejects_credential_in_url():
    with pytest.raises(ValueError):
        ModelConfig(endpoint='https://user:secret@example.com/chat/completions',model='x')
