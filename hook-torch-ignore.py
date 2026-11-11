# hook-torch-ignore.py
import sys
import types

def mock_module(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

# Блокируем ТОЛЬКО сломанный модуль _numpy и тяжелый _dynamo
mock_module("torch._numpy")
mock_module("torch._numpy._ufuncs")
mock_module("torch._numpy._util")
mock_module("torch._numpy._funcs")
mock_module("torch._numpy._dtypes")
mock_module("torch._numpy._dtypes_impl")

mock_module("torch._dynamo")

# torch.testing и torch.distributed МЫ НЕ ТРОГАЕМ.