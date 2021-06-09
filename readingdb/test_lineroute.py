import unittest
from readingdb.lineroute import LinePoint, LineRoute, linear_interp

class TestLineRoute(unittest.TestCase):

    def test_performs_lnear_interpolation_on_real_points(self):
        start_point = LinePoint.from_point({
            "Timestamp": 1568113911576,
            "Latitude": -37.8714232,
            "Longitude": 145.2450816
        })
        end_point = LinePoint.from_point({
            "Timestamp": 1618113911576,
            "Latitude": -37.8744232,
            "Longitude": 145.7450816
        })
        pnts = [
            start_point,
            end_point
        ]

        r = LineRoute(pnts, interp_alg=linear_interp)
        interp = r.point_at(1568113911576)
        self.assertEqual(interp, start_point)

        r = LineRoute(pnts, interp_alg=linear_interp)
        interp = r.point_at(1617779685467)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 1617779685467,
            "Latitude": -37.874403146433465,
            "Longitude": 145.74173933891
        }))

    def test_performs_lnear_interpolation_on_dummy_points(self):
        start_point = LinePoint.from_point({
            "Timestamp": 10,
            "Latitude": 10,
            "Longitude": 20
        })
        middle_point = LinePoint.from_point({
            "Timestamp": 20,
            "Latitude": 20,
            "Longitude": 40
        })
        end_point = LinePoint.from_point({
            "Timestamp": 120,
            "Latitude": 21,
            "Longitude": 50
        })
        pnts = [
            start_point,
            middle_point,
            end_point
        ]

        r = LineRoute(pnts, interp_alg=linear_interp)
        interp = r.point_at(10)
        self.assertEqual(interp, start_point)
        interp = r.point_at(20)
        self.assertEqual(interp, middle_point)
        interp = r.point_at(120)
        self.assertEqual(interp, end_point)
        interp = r.point_at(19)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 19,
            "Latitude": 19,
            "Longitude": 38
        }))
        interp = r.point_at(11)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 11,
            "Latitude": 11,
            "Longitude": 22
        }))
        interp = r.point_at(119)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 119,
            "Latitude": 20.99,
            "Longitude": 49.9
        }))


class TestInterpolation(unittest.TestCase):

    def test_linear_interpolation_returns_bookends(self):
        start_ts = 1568113911576
        end_ts = 1618113911576
        start_point = LinePoint.from_point({
            "Timestamp": start_ts,
            "Latitude": -37.8714232,
            "Longitude": 145.2450816
        })
        end_point = LinePoint.from_point({
            "Timestamp": end_ts,
            "Latitude": -37.8744232,
            "Longitude": 145.7450816
        })

        interp = linear_interp(start_point, end_point, start_ts)
        self.assertEqual(interp, start_point)

        interp = linear_interp(start_point, end_point, end_ts)
        self.assertEqual(interp, end_point)

    def test_linear_interpolation(self):
        start_point = LinePoint.from_point({
            "Timestamp": 200,
            "Latitude": -10.0,
            "Longitude": 150.0
        })
        end_point = LinePoint.from_point({
            "Timestamp": 300,
            "Latitude": -20.0,
            "Longitude": 100.0,
        })
        interp = linear_interp(start_point, end_point, 250)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 250,
            "Latitude": -15.0,
            "Longitude": 125.0,
        }))
        start_point = LinePoint.from_point({
            "Timestamp": 200,
            "Latitude": 20.0,
            "Longitude": 10.0
        })
        end_point = LinePoint.from_point({
            "Timestamp": 300,
            "Latitude": -20.0,
            "Longitude": 110.0,
        })
        interp = linear_interp(start_point, end_point, 210)
        self.assertEqual(interp, LinePoint.from_point({
            "Timestamp": 210,
            "Latitude": 16.0,
            "Longitude": 20.0,
        }))
