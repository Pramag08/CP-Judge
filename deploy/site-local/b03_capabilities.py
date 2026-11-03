"""Compile and run harmless capability/isolation probes with native executors.
No problem import, submission record or bridge grading request is involved.
"""
import json
import socket
import subprocess
import sys
from pathlib import Path
import yaml
from dmoj import judgeenv, executors

sys.argv = ['b03-capabilities', '-c', '/config.yml', '--only-executors', 'CPP11,CPP14,CPP17,CPP20,CPP23', '--no-ansi']
judgeenv.load_env(cli=True)
assert judgeenv.api_listen is None
executors.load_executors()
expected = {'CPP11': 201103, 'CPP14': 201402, 'CPP17': 201703, 'CPP20': 202002, 'CPP23': 202302}
assert set(executors.executors) == set(expected)
assert dict(judgeenv.env.runtime) == yaml.safe_load(Path('/judge-runtime-paths.yml').read_text())['runtime']
results = {}

def execute(key, source):
    executor = executors.executors[key].Executor('b03_diagnostic', source.encode())
    try:
        proc = executor.launch(time=3, memory=131072, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(b'')
        assert proc.returncode == 0 and not proc.is_tle and not proc.is_mle and not proc.protection_fault, (key, proc.returncode, err)
        assert not err, err
        return out.decode().strip()
    finally:
        executor.cleanup()

isolation = r'''
#include <sys/socket.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <iostream>
int main() {
  const int families[] = {AF_INET,AF_INET6,AF_UNIX};
  for (int family: families) for(int type: {SOCK_STREAM,SOCK_DGRAM}) {
    errno=0; int fd=socket(family,type,0);
    if(fd>=0 || errno!=EACCES) return 10;
  }
  errno=0; int fd=open("/config.yml",O_RDONLY);
  if(fd>=0 || errno!=EACCES) return 11;
  std::cout << "six_socket_attempts_and_config_read_denied";
}
'''
for key, value in expected.items():
    source = '#include <iostream>\n'
    if key == 'CPP23':
        source += '#include <expected>\nstatic_assert(__cplusplus == 202302L);\nint main(){ std::expected<int,int> value=42; std::cout<<__cplusplus<<":"<<value.value(); }\n'
        want = str(value) + ':42'
    else:
        source += 'int main(){ std::cout<<__cplusplus; }\n'
        want = str(value)
    assert execute(key, source) == want
    assert execute(key, isolation) == 'six_socket_attempts_and_config_read_denied'
    results[key] = {'cplusplus': value, 'compiler_versions': executors.executors[key].Executor.get_runtime_versions(),
                    'compiler_full_version': subprocess.check_output([executors.executors[key].Executor.get_command(), '-dumpfullversion'], text=True).strip(),
                    'sandbox_socket_denials': 6, 'private_config_read_denied': True,
                    'CPP23_expected_feature': key == 'CPP23'}
with socket.create_connection(('127.0.0.1',9999), timeout=3):
    pass
print('B03_RESULT=' + json.dumps({'status': 'PASS', 'executors': results,
      'supervisor_coordinator_tcp': True, 'worker_api_disabled': True,
      'pinned_runtime_mapping_exact': True, 'website_judging': 'NOT TESTED'}, indent=2))
