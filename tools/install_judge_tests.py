"""Install expected verdicts for the supported DMOJ `test` command."""
from pathlib import Path
import yaml
import zipfile

SUM = '#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"  \\n";}\n'
RE = '#include <cstdlib>\nint main(){std::abort();}'
TLE = 'int main(){for(;;) asm volatile("");}'
WA = '#include <iostream>\nint main(){std::cout<<-999;}'


def install(directory, kind, real_source=None):
    directory = Path(directory)
    conf = yaml.safe_load((directory / 'init.yml').read_text())
    tests = []
    sources = [('accepted', SUM, 'AC', None), ('wrong', WA, 'WA', None),
               ('runtime', RE, 'RTE', None), ('timeout', TLE, 'TLE', None)]
    if kind == 'multiple':
        sources[0] = ('accepted', '#include <iostream>\nint main(){std::cout<<2;}', 'AC', None)
        sources.append(('alternative', '#include <iostream>\nint main(){std::cout<<4;}', 'AC', None))
        sources.append(('presentation', '#include <iostream>\nint main(){std::cout<<"2 extra";}', 'WA', None))
    if kind == 'groups':
        sources = [('accepted', SUM, ['AC']*3, [30,50,20]),
                   ('easy_only', '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<(a==2?a+b:-999);}', ['AC','WA','WA'], [30,0,0]),
                   ('dependency', '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<(a==2?-999:a+b);}', ['WA','SC','AC'], [0,0,20]),
                   ('wrong', WA, ['WA','SC','WA'], [0,0,0])]
    if real_source:
        if kind != 'gaming-grid':
            raise ValueError('real judging probes are currently defined only for gaming-grid')
        # Valid NO tokens reach the semantic mismatch path; -999 only triggers PE.
        # The checker accepts case-insensitive tokens, as do we when deriving expectations.
        with zipfile.ZipFile(directory / conf['archive']) as data:
            expected = ['WA' if 'YES' in data.read(case['out']).decode().upper().split() else 'AC'
                        for case in conf['test_cases']]
        if 'WA' not in expected:
            raise ValueError('all-NO probe has no genuine mismatch in this package')
        wrong = '#include <iostream>\nint main(){int t;std::cin>>t;while(t--)std::cout<<"NO\\n";}'
        sources[1] = ('wrong_answer', wrong, expected, None)
        sources[0] = ('reference', Path(real_source).read_text(), 'AC', None)
    (directory / 'solutions').mkdir(exist_ok=True)
    for label, source, expected, scores in sources:
        filename = f'solutions/{label}.cpp'
        (directory / filename).write_text(source)
        test = dict(label=label, source=filename, language='CPP20', time=conf['time_limit'], memory=conf['memory_limit'])
        if isinstance(expected, list):
            test['cases'] = expected
        else:
            test['expect'] = expected
        if label == 'wrong_answer':
            test['feedback'] = ''  # Testlib WA (1), not PE (2, 'Presentation Error')
        if scores is not None:
            test['score_cases'] = scores
        tests.append(test)
    conf['tests'] = tests
    (directory / 'init.yml').write_text(yaml.safe_dump(conf, sort_keys=False))
