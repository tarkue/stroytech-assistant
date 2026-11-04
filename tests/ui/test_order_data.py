"""Order parsing remains available through stroytech.ui."""
import unittest
from stroytech.ui import parse_order


class OrderFormTests(unittest.TestCase):
    def test_unknown_values_remain_unknown(self):
        order=parse_order({'work':'Подъем','soil':'Неизвестно','weather':'Дождь','duration_hours':'2,5'})
        self.assertEqual(order['work'],'lifting')
        self.assertIsNone(order['soil'])
        self.assertIsNone(order['groundwater'])
        self.assertEqual(order['duration_hours'],2.5)

    def test_positive_mass_radius_and_finite_numbers(self):
        for field,value in [('duration_hours','0'),('load_t','0'),('radius_m','0'),('load_t','-1'),('radius_m','nan'),('angle_deg','91')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_order({'duration_hours':'8',field:value})
        order=parse_order({'duration_hours':'8','load_t':'','radius_m':'','angle_deg':''})
        self.assertIsNone(order['load_t'])
        self.assertIsNone(order['radius_m'])
