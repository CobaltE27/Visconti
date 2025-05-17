from django.test import TestCase
from . import models
from . import views
from django.test.client import RequestFactory

goods = [models.Good.GRAIN, models.Good.CLOTH, models.Good.DYE, models.Good.SPICE, models.Good.FURS]
# Create your tests here.
class AllCostTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="", deck="", chooser="", bidder="")
        models.Player.objects.create(name="first", money=0, lots="10x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="5x 3x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="1x 1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="fourth", money=0, lots="0x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_scoring(self):
        models.score_day()
        # print("")
        # for p in models.get_players():
        #     print(p.name + str(p.money))
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
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="", deck="", chooser="", bidder="")
        models.Player.objects.create(name="first", money=0, lots="10x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="5x 5x 5x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="7x 3x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_scoring(self):
        models.score_day()
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")
        # print("")
        # for p in models.get_players():
        #     print(p.name + str(p.money))

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

class PyramidTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="", deck="", chooser="", bidder="")
        models.Player.objects.create(name="first", money=0, lots="30g", current_bid=0, grain=7, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="10g 10f 5f", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="1d 1d", current_bid=0, grain=0, cloth=0, dye=3, spice=0, furs=0)

    def test_pyramid_scoring(self):
        models.score_day()
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")

        self.assertEqual(first.grain, 7)
        self.assertEqual(second.grain, 1)
        self.assertEqual(second.furs, 2)
        self.assertEqual(third.dye, 5)

        self.assertEqual(first.money, 30 + (5 + 2 + 2 + (20 + 10) + 5))
        self.assertEqual(second.money, 15 + (5 + 2 + 10 + 5 + 5))
        self.assertEqual(third.money, 0 + (5 + (5 + 10) + 2 + 0 + 5))

class CostOfLotsTestCase(TestCase):
    def setUp(self):
        self.tenSingle = "10x"
        self.tenMult = "7x 3x"
        self.fiveMult = "1x 1x 1x 1x 1x"

    def test_cost_of_lots(self):
        self.assertEqual(models.cost_of_lots(self.tenSingle), 10)
        self.assertEqual(models.cost_of_lots(self.tenMult), 10)
        self.assertEqual(models.cost_of_lots(self.fiveMult), 5)

class MoveToNextBidderTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="1x 1x 1x", deck="", chooser="first", bidder="second")
        models.Player.objects.create(name="first", money=0, lots="1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="1x 1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_next_bidder(self):
        models.move_to_next_bidder()
        host = models.get_host()
        self.assertEqual(host.bidder, "first")

class MoveToNextChooserTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="", deck="", chooser="second", bidder="second")
        models.Player.objects.create(name="first", money=0, lots="1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=0, lots="1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=0, lots="1x 1x 1x 1x 1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_next_chooser(self):
        models.move_to_next_chooser()
        host = models.get_host()
        self.assertEqual(host.chooser, "first")

class ReceiveBidEndBiddingTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="1x 1x 2x", deck="10x", chooser="second", bidder="second")
        models.Player.objects.create(name="first", money=0, lots="1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=10, lots="1x 1x", current_bid=10, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=7, lots="1x 1x 1x 1x 1x", current_bid=7, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_end_bidding(self):
        models.end_bidding_phase()
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")
        host = models.get_host()

        self.assertEqual(first.money, 30 + (5 * 5))
        self.assertEqual(second.money, 15 + (5 * 5))
        self.assertEqual(third.money, 7 + 0 + (5 * 5))
        self.assertEqual(first.current_bid, 0)
        self.assertEqual(second.current_bid, 0)
        self.assertEqual(third.current_bid, 0)

        self.assertEqual(host.phase, models.Phase.CHOOSING)
        self.assertEqual(host.day, 2)
        self.assertEqual(host.group_lots, "")
        self.assertEqual(host.chooser, "third")
        self.assertEqual(host.bidder, "first")
        self.assertEqual(models.count_lots(host.deck), 18)

class ReceiveBidChoosingTestCase(TestCase):
    def setUp(self):
        models.Host.objects.create(localIP="10.0.0.x", phase=models.Phase.BIDDING, day=1, group_lots="1x", deck="10x", chooser="second", bidder="second")
        models.Player.objects.create(name="first", money=0, lots="1x", current_bid=0, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="second", money=10, lots="1x 1x", current_bid=10, grain=0, cloth=0, dye=0, spice=0, furs=0)
        models.Player.objects.create(name="third", money=7, lots="1x 1x 1x 1x 1x", current_bid=7, grain=0, cloth=0, dye=0, spice=0, furs=0)

    def test_choosing(self):
        models.end_bidding_phase()
        first = models.Player.objects.get(name="first")
        second = models.Player.objects.get(name="second")
        third = models.Player.objects.get(name="third")
        host = models.get_host()

        self.assertEqual(first.money, 0)
        self.assertEqual(second.money, 0)
        self.assertEqual(third.money, 7)

        self.assertEqual(host.phase, models.Phase.CHOOSING)
        self.assertEqual(host.day, 1)
        self.assertEqual(host.group_lots, "")
        self.assertEqual(host.chooser, "first")
        self.assertEqual(host.deck, "10x")