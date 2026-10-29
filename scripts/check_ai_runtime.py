"""Verify running local AI boundaries. Never displays credentials or submits inference/orders."""

import json
import shutil
import subprocess

CODE = r"""
import importlib.util,json,os,socket,time,uuid
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from redis.exceptions import NoPermissionError
from packages.ai.settings import GatewaySettings
from packages.ai.worker import Worker
assert os.getuid()==10001
assert not any(n.startswith(('AUTH_','AWS_','DOCKER_','MARKET_')) for n in os.environ)
assert importlib.util.find_spec('apps') is None
assert not os.path.exists('/var/run/docker.sock')
w=Worker(GatewaySettings())
try:
 assert w.queue.ping()
 key='ai:boundary-check:'+uuid.uuid4().hex
 w.queue.set(key,'DISPOSABLE_PROOF',ex=10)
 assert w.queue.get(key)==b'DISPOSABLE_PROOF'
 try: w.queue.get('research:forbidden')
 except NoPermissionError: pass
 else: raise AssertionError('Unscoped Redis access')
 for table in ('users','risk_profile_versions','research_experiments'):
  with w.store.engine.connect() as db:
   try: db.execute(text('SELECT id FROM '+table))
   except DBAPIError as exc:
    assert getattr(exc.orig,'sqlstate',None)=='42501'
   else: raise AssertionError('Unscoped SQL access')
 def denied(host,port):
  try:
   with socket.create_connection((host,port),timeout=2): return False
  except OSError: return True
 assert all(denied(host,8000) for host in API_ADDRESSES)
 assert denied('api',8000)
 assert denied('169.254.169.254',80)
 assert denied('1.1.1.1',443)
 with socket.create_connection(('172.30.64.2',8888),timeout=2) as proxy:
  proxy.sendall(b'CONNECT 1.1.1.1:443 HTTP/1.1\r\nHost: 1.1.1.1:443\r\n\r\n')
  assert proxy.recv(1024).startswith(b'HTTP/1.1 403')
 print(json.dumps({'result':'PASSED_ACTUAL_RUNNING_CONTAINER_BOUNDARIES','uid':os.getuid(),'sql_scoped':True,'redis_roundtrip':True,'redis_non_ai_denied':True,'api_all_interfaces_unreachable':True,'metadata_unreachable':True,'direct_public_tcp_denied':True,'explicit_proxy_default_denied':True,'approved_endpoint_count':len(w.config.endpoints),'actual_model_inference':False}))
finally: w.close()
"""


def main() -> None:
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Docker CLI unavailable")
    result = subprocess.run(  # noqa: S603 -- fixed metadata-only inspection
        [
            docker,
            "inspect",
            "--format",
            "{{json .NetworkSettings.Networks}}",
            "ai-trading-research-api-1",
        ],
        capture_output=True,
        timeout=10,
        check=True,
    )
    addresses = [
        network["IPAddress"]
        for network in json.loads(result.stdout).values()
        if network["IPAddress"]
    ]
    code = CODE.replace("API_ADDRESSES", repr(addresses))
    checked = subprocess.run(  # noqa: S603 -- trusted fixed diagnostic, no model code or shell
        [docker, "exec", "-i", "ai-trading-research-ai-worker-1", "/app/.venv/bin/python", "-"],
        input=code.encode(),
        capture_output=True,
        timeout=30,
        check=False,
    )
    if checked.returncode:
        raise RuntimeError("Running AI boundary check failed; raw diagnostic withheld")
    print(checked.stdout.decode())


if __name__ == "__main__":
    main()
