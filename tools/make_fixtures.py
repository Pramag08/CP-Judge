"""Build deterministic, synthetic Polygon ZIPs; never execute generators."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHECK_TOKEN = r'''#include "testlib.h"
int main(int argc, char** argv) {
 registerTestlibCmd(argc, argv);
 while (!ans.seekEof()) {
  std::string expected = ans.readToken();
  if (ouf.seekEof() || ouf.readToken() != expected) quitf(_wa, "token mismatch");
 }
 if (!ouf.seekEof()) quitf(_pe, "extra tokens");
 quitf(_ok, "tokens match");
}
'''
CHECK_MULTI = r'''#include "testlib.h"
int main(int argc, char** argv) {
 registerTestlibCmd(argc, argv);
 int n = inf.readInt(), x = ouf.readInt();
 if (x < 1 || x > n || x % 2) quitf(_wa, "expected an even integer in [1,n]");
 if (!ouf.seekEof()) quitf(_pe, "extra tokens");
 quitf(_ok, "valid alternative answer");
}
'''


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ['tokens', 'multiple', 'groups']:
        groups = ''
        cases = [('2 3\n', '5\n'), ('7 4\n', '11\n'), ('8 9\n', '17\n')]
        if name == 'multiple':
            cases = [('6\n', '2\n'), ('10\n', '2\n'), ('8\n', '2\n')]
        if name == 'groups':
            groups = '''<groups>
<group name="easy" points="30" points-policy="complete-group"/>
<group name="hard" points="50" points-policy="complete-group"><dependencies><dependency group="easy"/></dependencies></group>
<group name="independent" points="20" points-policy="complete-group"/>
</groups>'''
        tests = ''.join(f'<test method="manual" sample="{"true" if i == 1 else "false"}"' +
                        (f' group="{["easy", "hard", "independent"][i-1]}"' if name == 'groups' else '') + '/>' for i in range(1, 4))
        xml = f'''<?xml version="1.0"?><problem short-name="{name}">
<names><name language="english" value="SYNTHETIC: {name}"/></names>
<statements><statement language="english" type="text/html" path="statements/english/problem.html"/></statements>
<judging input-file="" output-file=""><testset name="tests">
<time-limit>500</time-limit><memory-limit>67108864</memory-limit><test-count>3</test-count>
<input-path-pattern>tests/%02d</input-path-pattern><answer-path-pattern>tests/%02d.a</answer-path-pattern>
<tests>{tests}</tests>{groups}</testset></judging>
<assets><checker type="testlib"><source path="files/checker.cpp" type="cpp.g++17"/></checker></assets></problem>'''
        files = {'problem.xml': xml.encode(), 'files/checker.cpp': (CHECK_MULTI if name == 'multiple' else CHECK_TOKEN).encode(),
                 'files/testlib.h': (ROOT / 'fixtures/testlib/testlib.h').read_bytes(),
                 'statements/english/problem.html': (f'<h1>SYNTHETIC {name}</h1><p>' +
                    ('Print any even integer in [1,n].' if name == 'multiple' else 'Print the sum of two integers.') +
                    f'</p><pre>{cases[0][0]}</pre><pre>{cases[0][1]}</pre>').encode()}
        for i, (inp, ans) in enumerate(cases, 1):
            files[f'tests/{i:02}'] = inp.encode()
            files[f'tests/{i:02}.a'] = ans.encode()
        with zipfile.ZipFile(out / f'{name}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for path, data in sorted(files.items()):
                info = zipfile.ZipInfo(path, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)


if __name__ == '__main__':
    build(ROOT / 'build/fixtures')
