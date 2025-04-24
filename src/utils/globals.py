from enum import Enum


SDP_LOGO = ('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'
            'VatWrVr9r/oLCioDfP6dVysAAAAASUVORK5CYII=')

FILE_PIC_BASE_64 = ('iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAk1BMVEVHcEzJz9j/Vi/'
                    'jMQbo6+7FytL/VS/ovrbq6+/e4Obs9fvhZUfbLwnYy835UizR1N3/VjDM0tn9XzzHzdb'
                    '/79Dr7PD/VjDu7/PCyND8clO/xc7/WTP/UCjs7vL/SiL/RBrFy9T29/v//v7/8/D/ppP'
                    '/va709Pn/moP/3NX/ZEH/Uyz/xLf/0Mb/6eT/hGj/eFpHcEwgl6rUAAAAMXRSTlMA9NT7'
                    'TULPA/77+e9KZ/glnOze4f////////////////////////////////////8A2zK2aQAAA'
                    'clJREFUSMfN1e1ugjAUBuBuTkCdClsoaEthFGwpftz/3e0UxLFRCvuz7E1MQzhPzkEKIAR'
                    'x0TZJvPBnVu9LOGWIi/ZhNKyPVllgFi56+RjWAzhmT0YxDkbEOIjNwgLMwgaMwjaSUdg7G'
                    'IQVmKaa6DAU9g7H4VRTIw16WO50FxDv+6kOevd9JV69PFqMgTDxeolmgH68058Cdx5wvzp'
                    'sTzPAtuvgotfNOpwE681rK6B+MQOE682iEbp+LmgF1ANIJqMBCISe1W63O8wIlClHA4IJp'
                    'k1YqkNVszJFaXOcsvYslJE7aEPotYQIWIuiEAdKsCh0bupR8h2wIuec52dWw5rngpJLriP'
                    'YOKgoLfJDyQmpyvzGLmdcVVVXYAQsFQ1QlPASQArDKwuQZ5lLWnO4PiYlk3pGbhtJSllW6'
                    'QNceFmX9ZWOdYBpUsowqzl+jMQYo3gc3CghBEDVXbQ+xpZrAABr+7cWFHPJeuV90PzUQVT'
                    '6dioB96/Qk4urGgJfN+22Rm+LNFvjvivuW4MQXz8PvuO8zdl8b47j6+fB/c1LoH3k5gP3/'
                    '77I0NKLksiaJPKWfZAFq4kEWR/s4+xoT5zF+/4naBvEEwnub8pP7R+maUCbATwAAAAASUVO'
                    'RK5CYII=')

class AppState(Enum):
    """Enum for the AppState."""
    FILE_SELECTION = "file_selection"
    PROCESSING = "processing"
    RESULTS = "results"
    COMPLETE = "complete"
    ERROR = "error"
