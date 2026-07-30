import random
import unittest

from events import EVENT_CHANCE, EVENTS, maybe_trigger_event


class _FakeRng:
    def __init__(self, randoms=(), choices=()):
        self._randoms = list(randoms)
        self._choices = list(choices)

    def random(self):
        return self._randoms.pop(0)

    def choice(self, seq):
        return self._choices.pop(0)


class MaybeTriggerEventTest(unittest.TestCase):
    def test_low_roll_triggers_the_chosen_event(self):
        rng = _FakeRng(randoms=[0.01], choices=[EVENTS[2]])
        self.assertEqual(maybe_trigger_event(rng), EVENTS[2])

    def test_boundary_roll_at_threshold_does_not_trigger(self):
        rng = _FakeRng(randoms=[EVENT_CHANCE])
        self.assertIsNone(maybe_trigger_event(rng))

    def test_high_roll_does_not_trigger(self):
        rng = _FakeRng(randoms=[0.9])
        self.assertIsNone(maybe_trigger_event(rng))


class MaybeTriggerEventPropertyTest(unittest.TestCase):
    def test_result_always_none_or_a_real_event(self):
        event_ids = {event["id"] for event in EVENTS}
        for seed in range(200):
            result = maybe_trigger_event(random.Random(seed))
            if result is not None:
                self.assertIn(result["id"], event_ids)
                self.assertIn("text", result)
                self.assertIn("food_delta", result)

    def test_triggers_roughly_at_expected_rate(self):
        triggered = sum(
            1 for seed in range(2000) if maybe_trigger_event(random.Random(seed)) is not None
        )
        rate = triggered / 2000
        self.assertTrue(abs(rate - EVENT_CHANCE) < 0.03)

    def test_every_event_has_required_fields(self):
        for event in EVENTS:
            self.assertIn("id", event)
            self.assertIn("text", event)
            self.assertIn("food_delta", event)

    def test_event_ids_are_unique(self):
        ids = [event["id"] for event in EVENTS]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
