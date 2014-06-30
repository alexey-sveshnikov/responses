from __future__ import (
    absolute_import, print_function, division, unicode_literals
)

import requests
import responses
import pytest

from requests.exceptions import ConnectionError


def assert_reset():
    assert len(responses._default_mock._urls) == 0
    assert len(responses.calls) == 0


def assert_response(resp, body=None):
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == body


def test_response():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com', body=b'test')
        resp = requests.get('http://example.com')
        assert_response(resp, 'test')
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'http://example.com/'
        assert responses.calls[0].response.content == b'test'

    run()
    assert_reset()


def test_connection_error():
    @responses.activate
    def run():
        responses.add(responses.GET, 'http://example.com')

        with pytest.raises(ConnectionError):
            requests.get('http://example.com/foo')

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'http://example.com/foo'
        assert type(responses.calls[0].response) is ConnectionError

    run()
    assert_reset()


def test_match_querystring():
    @responses.activate
    def run():
        url = 'http://example.com?test=1'
        responses.add(
            responses.GET, url,
            match_querystring=True, body=b'test')
        resp = requests.get(url)
        assert_response(resp, 'test')

    run()
    assert_reset()


def test_match_querystring_error():
    @responses.activate
    def run():
        responses.add(
            responses.GET, 'http://example.com/?test=1',
            match_querystring=True)

        with pytest.raises(ConnectionError):
            requests.get('http://example.com/foo/?test=2')

    run()
    assert_reset()


def test_accept_string_body():
    @responses.activate
    def run():
        url = 'http://example.com/'
        responses.add(
            responses.GET, url, body='test')
        resp = requests.get(url)
        assert_response(resp, 'test')

    run()
    assert_reset()


def test_side_effect_callback():
    @responses.activate
    def run():
        def callback(request):
            assert request.params['one'] == '1'
            assert request.data['two'] == '2'
            assert request.method == 'POST'
            return responses.Response(
                body='test',
            )

        url = 'http://example.com/'
        responses.add(
            responses.POST, url,
            side_effect=callback
        )
        resp = requests.post(url, params={'one': 1}, data={'two': 2})
        assert_response(resp, 'test')

    run()
    assert_reset()


def test_side_effect_sequence():
    @responses.activate
    def run():
        url = 'http://example.com/'
        responses.add(
            responses.GET, url,
            side_effect=[
                responses.Response('test1'),
                responses.Response('test2'),
            ],
        )
        resp = requests.get(url)
        assert_response(resp, 'test1')

        resp = requests.get(url)
        assert_response(resp, 'test2')

    run()
    assert_reset()
