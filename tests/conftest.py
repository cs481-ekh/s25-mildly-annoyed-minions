def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run",
    )

    config.addinivalue_line(
        "markers", "quick: mark test as quick to run",
    )