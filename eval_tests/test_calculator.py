import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent / "test_repo"

sys.path.insert(0, str(REPOSITORY))

from calculator import add, divide


def test_add():
    assert add(2, 3) == 5


def test_normal_division():
    assert divide(10, 2) == 5


def test_division_by_zero():
    try:
        divide(10, 0)
    except ValueError:
        return

    assert False, "divide() must raise ValueError for division by zero"