"""Campaign call budget for the agent provider: counted once per answer, replay free, hard stop at the limit."""
import json
import pytest
from exam_mastery.providers import AgentProvider, CallLedger
from exam_mastery.budget import BudgetBlocked


def _answer(run, role, prompt, obj):
    import hashlib
    key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    (run / 'agent_io').mkdir(parents=True, exist_ok=True)
    (run / 'agent_io' / f'{role}-{key}.answer.json').write_text(json.dumps(obj))


def test_counts_once_replays_free_and_blocks(tmp_path, monkeypatch):
    led = tmp_path / 'ledger.json'
    led.write_text(json.dumps({'schema': 'em-call-ledger-v1', 'limit': 2, 'calls': []}))
    monkeypatch.setenv('EXAM_MASTERY_CALL_LEDGER', str(led))
    p = AgentProvider()
    for i, run in enumerate(['r1', 'r2']):
        _answer(tmp_path / run, 'author', 'P', {'a': 1})       # same answer in two runs = one call
        assert p.ask('author', 'P', tmp_path / run) == {'a': 1}
    assert len(json.loads(led.read_text())['calls']) == 1
    _answer(tmp_path / 'r1', 'review', 'Q', {'b': 2})
    p.ask('review', 'Q', tmp_path / 'r1')
    assert CallLedger(led).used() == 2
    with pytest.raises(BudgetBlocked) as e:                      # at the limit: no new prompt is even requested
        p.ask('solutions', 'R', tmp_path / 'r1')
    assert 'budget exhausted' in str(e.value)
    assert not list((tmp_path / 'r1' / 'agent_io').glob('solutions-*.prompt.txt'))
    _answer(tmp_path / 'r1', 'solutions', 'R', {'c': 3})          # an answer placed anyway is not consumed
    with pytest.raises(BudgetBlocked):
        p.ask('solutions', 'R', tmp_path / 'r1')


def test_pre_campaign_answers_are_free(tmp_path, monkeypatch):
    import hashlib
    _answer(tmp_path / 'r', 'author', 'P', {'a': 1})
    sha = hashlib.sha256(next((tmp_path / 'r' / 'agent_io').glob('*.answer.json')).read_bytes()).hexdigest()
    led = tmp_path / 'l.json'
    led.write_text(json.dumps({'limit': 0, 'calls': [], 'pre_campaign_answers': [sha]}))
    monkeypatch.setenv('EXAM_MASTERY_CALL_LEDGER', str(led))
    assert AgentProvider().ask('author', 'P', tmp_path / 'r') == {'a': 1}
