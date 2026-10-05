from llm import client


def test_native_chat_returns_answer_without_reasoning(monkeypatch):
    requests = []

    def request(url, **kwargs):
        requests.append((url, kwargs))
        if url.endswith('/models'):
            return {'data': [{'id': 'hermes-free'}]}
        return {'output': [{'type': 'reasoning', 'content': 'private reasoning'},
                           {'type': 'message', 'content': 'READY'}]}

    monkeypatch.setattr(client, '_request_json', request)
    result = client._openai_compatible_local_response(
        {'task': {'goal': 'Reply READY'}}, 'lmstudio_windows',
        {'base_url': 'http://localhost:1234/v1', 'native_chat': True},
        'hermes-free', {'max_tokens': 32})
    assert result['result'] == 'READY'
    url, options = requests[-1]
    assert url == 'http://localhost:1234/api/v1/chat'
    assert options['payload']['reasoning'] == 'off'
    assert options['payload']['store'] is False
    assert options['payload']['max_output_tokens'] == 32


def test_native_chat_rejects_reasoning_without_answer(monkeypatch):
    monkeypatch.setattr(client, '_discover_local_model', lambda *a, **kw: 'hermes-free')
    monkeypatch.setattr(client, '_request_json', lambda *a, **kw: {
        'output': [{'type': 'reasoning', 'content': 'unfinished'}]})
    assert client._openai_compatible_local_response(
        {'task': {'goal': 'Reply READY'}}, 'lmstudio_windows',
        {'base_url': 'http://localhost:1234/v1', 'native_chat': True},
        'hermes-free', {}) is None
