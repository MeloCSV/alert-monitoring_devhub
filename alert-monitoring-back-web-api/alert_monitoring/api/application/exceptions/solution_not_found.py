from fwkpy_lib_utils.common.i18n.internationalization import get_message
from fwkpy_lib_utils.exceptions import MercadonaBusinessException


class SolutionNotFoundException(MercadonaBusinessException):

    def __init__(self, solution: str):
        self._error_code = '00404'
        self._message = get_message('exceptions', 'solution_not_found', solution=solution)
        super().__init__(self._message, self._error_code)

    def __str__(self):
        return self._message
