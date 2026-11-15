"""Vorbereitete, anbieterneutrale API-Schnittstelle für einen späteren Tutor-Dienst – standardmäßig AUS.

Ein echter Aufruf erfordert alle drei Bedingungen: ausdrückliche Zustimmung (opt-in), ein freigegebenes Budget in
NEXT_ACTION.json (`budget.tutor_api_calls_authorised` > 0) und einen registrierten Anbieter. Derzeit ist kein Anbieter
registriert und kein Budget freigegeben; `ask` wirft deshalb immer `TutorAPIDisabled`. Es gibt keinen Netzwerkcode.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class TutorAPIDisabled(RuntimeError):
    pass


@dataclass
class Policy:
    opt_in: bool = False
    budget_calls: int = 0
    used_calls: int = 0
    send_learner_state: bool = False          # Datenschutz: Lernstand nur mit gesonderter Zustimmung
    max_context_chars: int = 60000
    providers: dict = field(default_factory=dict)  # name -> callable(messages) ; leer = nichts registriert

    @classmethod
    def from_next_action(cls, path: Path) -> 'Policy':
        n = json.loads(Path(path).read_text(encoding='utf-8'))
        return cls(budget_calls=int(n.get('budget', {}).get('tutor_api_calls_authorised', 0) or 0))


def ask(policy: Policy, provider: str, context: dict, message: str) -> str:
    if not policy.opt_in:
        raise TutorAPIDisabled('kein opt-in')
    if policy.used_calls >= policy.budget_calls:
        raise TutorAPIDisabled(f'kein Budget ({policy.used_calls}/{policy.budget_calls})')
    if provider not in policy.providers:
        raise TutorAPIDisabled(f'Anbieter {provider!r} nicht registriert')
    ctx = dict(context)
    if not policy.send_learner_state:
        ctx['learner_state'] = None
    payload = json.dumps(ctx, ensure_ascii=False)[:policy.max_context_chars]
    policy.used_calls += 1
    return policy.providers[provider]([{'role': 'system', 'content': payload}, {'role': 'user', 'content': message}])
