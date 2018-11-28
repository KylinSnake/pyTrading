import unittest
from Indicators import *


class IndicatorTest(unittest.TestCase):
    def test_EMA(self):
        sample = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
        ema = EMA(sample, 4)
        self.assertEqual(ema[0], 1.0)
        for i in (1, 8):
            self.assertEqual(ema[i], (ema[i-1] * 0.6 + sample[i] * 0.4))

    def test_TR(self):
        low = np.array([1.0, 3.0, 4.0, 7.0, 4.0, 6.0, 8.0])
        high = np.array([4.0, 4.0, 5.0, 8.0, 5.0, 10.0, 9.0])
        close = np.array([2.5, 3.6, 4.7, 7.7, 5.0, 8.2, 8.4])
        tr = TR(high, low, close)
        self.assertEqual(tr[0], 3.0)
        self.assertEqual(tr[1], 1.5)
        self.assertEqual(tr[2], 1.4)
        self.assertEqual(tr[3], 3.3)
        self.assertEqual(tr[4], 3.7)
        self.assertEqual(tr[5], 5.0)
        self.assertEqual(tr[6], 1.0)

    def test_DM(self):
        low = np.array([1.0, 3.0, 4.0, 7.0, 4.0, 2.0, 1.0])
        high = np.array([4.0, 4.0, 5.0, 8.0, 5.0, 6.0, 9.0])
        (pdm, ndm) = DM(high, low)

        self.assertEqual(pdm[0], 0.0)
        self.assertEqual(ndm[0], 0.0)

        self.assertEqual(pdm[1], 0.0)
        self.assertEqual(ndm[1], 0.0)

        self.assertEqual(pdm[2], 1.0)
        self.assertEqual(ndm[2], 0.0)

        self.assertEqual(pdm[3], 3.0)
        self.assertEqual(ndm[3], 0.0)

        self.assertEqual(pdm[4], 0.0)
        self.assertEqual(ndm[4], 3.0)

        self.assertEqual(pdm[5], 0.0)
        self.assertEqual(ndm[5], 2.0)

        self.assertEqual(pdm[6], 3.0)
        self.assertEqual(ndm[6], 0.0)

    def test_DI(self):
        ndm = np.array([1.0, 0.0, 0.0, 3.0])
        pdm = np.array([0.0, 2.0, 0.0, 0.0])
        tr = np.array([2.0, 3.0, 2.0, 4.0])
        (pdi, ndi) = DI(tr, 1, pdm, ndm)
        tr_n = EMA(tr, 1)
        e_pdi = EMA(pdm, 1)
        e_ndi = EMA(ndm, 1)
        self.assertEqual(pdi[0], e_pdi[0]/tr_n[0])
        self.assertEqual(ndi[0], e_ndi[0]/tr_n[0])

        self.assertEqual(pdi[1], e_pdi[1]/tr_n[1])
        self.assertEqual(ndi[1], e_ndi[1]/tr_n[1])

        self.assertEqual(pdi[2], e_pdi[2] / tr_n[2])
        self.assertEqual(ndi[2], e_ndi[2] / tr_n[2])

        self.assertEqual(pdi[3], e_pdi[3] / tr_n[3])
        self.assertEqual(ndi[3], e_ndi[3] / tr_n[3])

    def test_past_days(self):
        sample = np.array([1.0, 4.0, 3.0, 2.0, 5])
        ret = value_of_past_days_with_today(sample, 3, lambda a: a[1])
        self.assertEqual(np.isnan(ret[0]), True)
        self.assertEqual(np.isnan(ret[1]), True)
        self.assertEqual(ret[2], 4.0)
        self.assertEqual(ret[3], 3.0)
        self.assertEqual(ret[4], 2.0)

    def test_max_past_days(self):
        sample = np.array([1.0, 4.0, 3.0, 2.0, 5.0])
        ret = maximum_past_days_with_today(sample, 3)
        self.assertEqual(np.isnan(ret[0]), True)
        self.assertEqual(np.isnan(ret[1]), True)
        self.assertEqual(ret[2], 4.0)
        self.assertEqual(ret[3], 4.0)
        self.assertEqual(ret[4], 5.0)

    def test_cci(self):
        pass

    def test_sar(self):
        pass

    def test_diverge(self):
        a = np.array([1,4,3,6,7,5,10])
        b = np.array([10,5,4,6,5,2,3])
        ret = Diverge(a, b, True)
        self.assertEqual(ret, (True, 1, -1))
        ret = Diverge(-a, -b, False)
        self.assertEqual(ret, (True, -1, 1))

if __name__ == '__main__':
    unittest.main()
