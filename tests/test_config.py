"""Settings precedence and secret handling, without touching the local config."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from stroytech.config import load_settings

class ConfigTests(unittest.TestCase):
    def settings(self, folder, env=None, **kwargs):
        with patch.dict(os.environ,env or {},clear=True), patch('stroytech.config.CONFIG_PATH',Path(folder)/'config.toml'):
            return load_settings(**kwargs)

    def test_defaults_and_nonsecret_file(self):
        with TemporaryDirectory() as folder:
            self.assertEqual(self.settings(folder).model,'qwen2.5-coder:7b')
            Path(folder,'config.toml').write_text('provider="ollama"\nmodel="local-model"\ntimeout=30\n')
            result=self.settings(folder)
            self.assertEqual((result.provider,result.model,result.timeout),('ollama','local-model',30))

    def test_env_and_explicit_precedence_and_repr(self):
        with TemporaryDirectory() as folder:
            Path(folder,'config.toml').write_text('provider="ollama"\nmodel="file-model"\ntimeout=20\n')
            env=dict(STROYTECH_PROVIDER='openrouter',OPENROUTER_MODEL='vendor/model',OPENROUTER_API_KEY='test-secret',STROYTECH_TIMEOUT='40')
            result=self.settings(folder,env)
            self.assertEqual((result.provider,result.model,result.timeout),('openrouter','vendor/model',40))
            self.assertNotIn('test-secret',repr(result))
            self.assertEqual(self.settings(folder,env,provider='ollama').provider,'ollama')

    def test_missing_credentials_invalid_values_and_secret_file(self):
        with TemporaryDirectory() as folder:
            for env in [dict(STROYTECH_PROVIDER='wrong'),dict(STROYTECH_TIMEOUT='nan'),dict(STROYTECH_TIMEOUT='0'),dict(STROYTECH_TIMEOUT='601'),dict(STROYTECH_PROVIDER='openrouter'),dict(STROYTECH_PROVIDER='openrouter',OPENROUTER_MODEL='vendor/model')]:
                with self.subTest(env=env),self.assertRaises(ValueError): self.settings(folder,env)
            Path(folder,'config.toml').write_text('api_key="do-not-store-here"\n')
            with self.assertRaises(ValueError): self.settings(folder)

    def test_read_settings_allows_missing_credentials_without_relaxing_load(self):
        from stroytech.config import read_settings
        with TemporaryDirectory() as folder,patch('stroytech.config.CONFIG_PATH',Path(folder)/'missing.toml'),patch.dict(os.environ,{},clear=True):
            settings=read_settings('openrouter')
            self.assertEqual((settings.provider,settings.model,settings.api_key),('openrouter','',''))
            with self.assertRaises(ValueError): load_settings('openrouter')
            with patch.dict(os.environ,{'OPENROUTER_MODEL':'vendor/model'}):
                self.assertEqual(read_settings('openrouter').model,'vendor/model')
            with patch.dict(os.environ,{'OPENROUTER_API_KEY':'private-test-key'}):
                self.assertTrue(read_settings('openrouter').api_key)
                self.assertNotIn('private-test-key',repr(read_settings('openrouter')))
