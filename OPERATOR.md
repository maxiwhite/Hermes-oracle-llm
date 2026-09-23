# Hermes local operator

Start from PowerShell:

```powershell
& 'C:\Users\max\Hermes-oracle-llm\start-hermes.cmd'
```

Enter a task at the Hermes prompt. Type `exit` to stop.

Other modes of the same launcher:

- `--task "Draft a short description for a used watch."`: one local model response.
- `--smoke`: create a synthetic resale draft, verify persistence, and request a real model answer. Synthetic data goes into a separate smoke directory and nothing is published.
- `--employee status`: inspect the local employee queue without loading a model.
- `--employee validate`: validate the local employee files.
- `--employee brain "Prepare this watch for resale"`: classify and plan a task locally.
- `--doctor`: check the local model and API configuration.
- `--serve`: serve the existing Hermes API at http://127.0.0.1:8000.
- `--freebuff`: hand this Hermes project to the authenticated Freebuff CLI without starting LM Studio.

To use the Freebuff bridge, run `start-hermes.cmd --freebuff`. Freebuff opens with `C:\Users\max\Hermes-oracle-llm` as its working project and keeps its own identity, account, model limits, and session history separate from Hermes.

The default model is Qwen3 1.7B Q4_K_M, with a 2,048-token context and reasoning disabled through LM Studio's native chat API. This is the most responsive useful local configuration on this computer. Startup uses explicit Python and LM Studio paths, does not download models, and does not enable paid fallback. The verified Qwen3.5 4B file is retained for optional heavier jobs, but it is deliberately not the default because CPU-only answers take about a minute or longer. The full Hermes Desktop prompt requires more context than this laptop can load efficiently; use the project launcher for local work or a cloud provider for the full desktop agent.

The launcher uses `.venv\Scripts\python.exe`; `HERMES_PYTHON` can override it. Python 3.11 and packages openai, python-dotenv, fastapi, uvicorn, pytest and httpx are installed. Runtime state is separate from the repository at `%LOCALAPPDATA%\HermesOracle`, unless `HERMES_DATA_DIR` is set.

The operator provides local text assistance and the existing employee/resale routines. Natural-language chat does not grant arbitrary computer control, and a listing draft does not mean it has been published. G0DM0D3 remains a preserved historical backup, not a verified running interface.

The restored brain and memory integration came from the original local backup. Source backups remain under Documents\Codex; no commits, pushes or publication were performed by this setup.
