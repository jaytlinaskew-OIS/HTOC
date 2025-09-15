""" standard """
import operator

""" third-party """
from enum import Enum


class FilterSetOperator(Enum):
    """ """
    # Query Set Operator
    AND = 'and'
    OR = 'or'


class FilterOperator(Enum):
    """ """
    # Query Operator
    EQ = operator.eq
    NE = operator.ne
    GT = operator.gt
    GE = operator.ge
    LT = operator.lt
    LE = operator.le
