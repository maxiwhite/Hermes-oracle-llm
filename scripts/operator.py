"""Local operator entrypoint: no model downloads or automatic cloud fallback."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def prepare_model():
    lms = Path.home() / '.lmstudio/bin/lms.exe'
    if not lms.is_file():
        raise RuntimeError('LM Studio CLI is missing.')
    subprocess.run([str(lms), 'daemon', 'up'], check=True, timeout=180)
    loaded = json.loads(subprocess.check_output([str(lms), 'ps', '--json'], text=True, timeout=30))
    if not any(m.get('identifier') == 'hermes-free' for m in loaded):
        subprocess.run([str(lms), 'load', 'qwen3.5-4b-verified', '--context-length', '2048',
                        '--identifier', 'hermes-free', '--gpu', 'off', '--parallel', '1'], check=True, timeout=180)
    subprocess.run([str(lms), 'server', 'start'], check=True, timeout=30)


def main():
    parser = argparse.ArgumentParser(description='Hermes local operator')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--task', help='Run one local model task')
    modes.add_argument('--smoke', action='store_true')
    modes.add_argument('--doctor', action='store_true')
    modes.add_argument('--serve', action='store_true')
    modes.add_argument('--employee', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.employee is not None:
        return subprocess.call([sys.executable, str(ROOT / 'hermes_employee.py'), *args.employee])
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    if config.get('cloud_enabled') or config.get('llm', {}).get('provider') != 'local_router':
        raise RuntimeError('Operator requires cloud_enabled=false and llm.provider=local_router.')
    prepare_model()
    if args.doctor or args.serve:
        return subprocess.call([sys.executable, str(ROOT / 'scripts/hermes_doctor.py'),
                                *(['--start'] if args.serve else [])])
    from core.executor import execute_task
    from memory.store import log_session

    def run(task):
        result = execute_task(task, config)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        log_session(task, result)
        return int(bool(result.get('error')) or not bool(result.get('result')))

    if args.smoke:
        from datetime import datetime, timezone
        from resale_agents.service import ResaleAgentService
        from runtime_state import resolve_data_root
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
        smoke_root = resolve_data_root() / 'smoke' / stamp
        os.environ['HERMES_DATA_DIR'] = str(smoke_root)
        service = ResaleAgentService()
        captured = service.capture_item({'title': 'SMOKE TEST Seiko watch', 'brand': 'Seiko',
                                        'condition': 'good', 'photos': ['test-front.jpg']})
        draft = service.run_until_approval(captured['data']['item']['item_id'])
        assert draft['data']['approval_required'] is True
        assert ResaleAgentService().health()['inventory_count'] == 1
        print(json.dumps({'resale_draft': 'PASS', 'persisted': True, 'published': False,
                          'smoke_data': str(smoke_root)}, indent=2), flush=True)
        os.environ['HERMES_DATA_DIR'] = str(smoke_root / 'inference')
        return run(f'Give one short tip for photographing a watch. Test {stamp}.')
    if args.task:
        return run(args.task)
    print('Hermes local operator. Enter a task; type exit to stop.', flush=True)
    while True:
        try:
            task = input('\nHermes> ').strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if task.lower() in {'exit', 'quit'}:
            return 0
        if task:
            run(task)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:
        print(f'[FAIL] {exc}', file=sys.stderr)
        raise SystemExit(1)
