from django.test import TestCase
from . import models

goods = [models.Good.grain, models.Good.cloth, models.Good.dye, models.Good.spice, models.Good.furs]
# Create your tests here.
class AllCostTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.bidding, day=1, group_lots="", deck="", chooser="", bidder="")
        models.Player.objects.create(name="first", money=0, lots="10x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="5x 3x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="1x 1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="fourth", money=0, lots="0x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_scoring(self):
        models.score_day()
        print("")
        for p in models.get_players():
            print(p.name + str(p.money))
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")
        fourth = models.Player.objects.get(name="fourth")

        self.assertEqual(first.lots, "")
        self.assertEqual(second.lots, "")
        self.assertEqual(third.lots, "")
        self.assertEqual(fourth.lots, "")
        for good in goods:
            self.assertEqual(getattr(first, good), 0)
            self.assertEqual(getattr(second, good), 0)
            self.assertEqual(getattr(third, good), 0)
            self.assertEqual(getattr(fourth, good), 0)
        self.assertEqual(first.money, 30 + (3 * 5)) # ranking points + 4-way ties (15 // 4) on all 5 pyramids
        self.assertEqual(second.money, 20 + (3 * 5))
        self.assertEqual(third.money, 10 + (3 * 5))
        self.assertEqual(fourth.money, 0 + (3 * 5))

class AllCostTiesTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.bidding, day=1, group_lots=0, deck="", chooser="", bidder="")
        models.Player.objects.create(name="first", money=0, lots="10x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="5x 5x 5x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="7x 3x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_scoring(self):
        models.score_day()
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")
        print("")
        for p in models.get_players():
            print(p.name + str(p.money))

        self.assertEqual(first.lots, "")
        self.assertEqual(second.lots, "")
        self.assertEqual(third.lots, "")
        for good in goods:
            self.assertEqual(getattr(first, good), 0)
            self.assertEqual(getattr(second, good), 0)
            self.assertEqual(getattr(third, good), 0)
        self.assertEqual(first.money, 7 + (5 * 5)) # ranking + 3-way ties on all pyramids
        self.assertEqual(second.money, 30 + (5 * 5))
        self.assertEqual(third.money, 7 + (5 * 5))

class CostOfLotsTestCase(TestCase):
    def setUp(self):
        self.tenSingle = "10x"
        self.tenMult = "7x 3x"
        self.fiveMult = "1x 1x 1x 1x 1x"

    def test_cost_of_lots(self):
        self.assertEqual(models.cost_of_lots(self.tenSingle), 10)
        self.assertEqual(models.cost_of_lots(self.tenMult), 10)
        self.assertEqual(models.cost_of_lots(self.fiveMult), 5)