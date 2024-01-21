import unittest

from simso.core.Task import PTask
from ..REORDER import compute_wcrt
from src.simso.model_builder import ModelBuilder


class SampleTask:
    def __init__(self, identifier, wcet, period, deadline):
        self.identifier = identifier
        self.wcet = wcet
        self.period = period
        self.deadline = deadline


class REORDERTest(unittest.TestCase):
    def test_compute_wcrt(self):
        # example 1 from the paper
        t1 = SampleTask(1, 4, 10, 10)
        t2 = SampleTask(2, 1, 20, 20)
        t3 = SampleTask(3, 1, 5, 5)
        t4 = SampleTask(4, 2, 12, 12)

        wcrt = compute_wcrt([t1, t2, t3, t4])
        self.assertEqual(10 - wcrt[1], 1)
        self.assertEqual(20 - wcrt[2], -2)
        self.assertEqual(5 - wcrt[3], -2)
        self.assertEqual(12 - wcrt[4], -1)

        # example 2 from the paper
        t1 = SampleTask(1, 1, 10, 10)
        t2 = SampleTask(2, 2, 20, 20)
        t3 = SampleTask(3, 2, 5, 5)

        wcrt = compute_wcrt([t1, t2, t3])
        self.assertEqual(10 - wcrt[1], 3)
        self.assertEqual(20 - wcrt[2], 5)
        self.assertEqual(5 - wcrt[3], 3)


if __name__ == "__main__":
    unittest.main()
