import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from .ranking import (
    FlightQuery,
    FlightResult,
    ScoredFlight,
    generate_tradeoff_note,
    label_flights,
    score_flight,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_flight(**kwargs):
    defaults = {
        "id": "f1",
        "source": "amadeus",
        "airline": "Delta",
        "flight_number": "DL100",
        "origin": "JFK",
        "destination": "MIA",
        "departure_datetime": "2026-04-01T08:00:00",
        "arrival_datetime": "2026-04-01T11:30:00",
        "duration_minutes": 210,
        "stops": 0,
        "price_total": 200.0,
        "baggage_carry_on": True,
        "baggage_checked": None,
        "booking_url": "https://flights.google.com/?q=test",
    }
    defaults.update(kwargs)
    return FlightResult(**defaults)


def _make_scored(flight_id, price, duration, stops, value_score, labels=()):
    flight = _make_flight(
        id=flight_id,
        price_total=price,
        duration_minutes=duration,
        stops=stops,
    )
    return ScoredFlight(flight=flight, value_score=value_score, labels=labels)


# ---------------------------------------------------------------------------
# score_flight tests
# ---------------------------------------------------------------------------

class FlightScoringTests(TestCase):

    def test_cheapest_flight_scores_higher_than_expensive(self):
        cheap = _make_flight(id="f1", price_total=100.0)
        expensive = _make_flight(id="f2", price_total=400.0)
        all_flights = [cheap, expensive]

        self.assertGreater(
            score_flight(cheap, all_flights),
            score_flight(expensive, all_flights),
        )

    def test_nonstop_scores_higher_than_one_stop(self):
        nonstop = _make_flight(id="f1", stops=0, price_total=200.0, duration_minutes=200)
        one_stop = _make_flight(id="f2", stops=1, price_total=200.0, duration_minutes=200)
        all_flights = [nonstop, one_stop]

        self.assertGreater(
            score_flight(nonstop, all_flights),
            score_flight(one_stop, all_flights),
        )

    def test_one_stop_scores_higher_than_two_stops(self):
        one_stop = _make_flight(id="f1", stops=1, price_total=200.0, duration_minutes=200)
        two_stops = _make_flight(id="f2", stops=2, price_total=200.0, duration_minutes=200)
        all_flights = [one_stop, two_stops]

        self.assertGreater(
            score_flight(one_stop, all_flights),
            score_flight(two_stops, all_flights),
        )

    def test_faster_flight_scores_higher(self):
        fast = _make_flight(id="f1", duration_minutes=120, price_total=200.0)
        slow = _make_flight(id="f2", duration_minutes=480, price_total=200.0)
        all_flights = [fast, slow]

        self.assertGreater(
            score_flight(fast, all_flights),
            score_flight(slow, all_flights),
        )

    def test_baggage_inclusion_increases_score(self):
        with_bag = _make_flight(id="f1", baggage_carry_on=True, price_total=200.0,
                                duration_minutes=200, stops=0)
        no_bag = _make_flight(id="f2", baggage_carry_on=False, price_total=200.0,
                              duration_minutes=200, stops=0)
        all_flights = [with_bag, no_bag]

        self.assertGreater(
            score_flight(with_bag, all_flights),
            score_flight(no_bag, all_flights),
        )

    def test_single_flight_scores_100(self):
        flight = _make_flight()
        score = score_flight(flight, [flight])
        self.assertEqual(score, 100.0)

    def test_score_always_clamped_to_0_100(self):
        flight = _make_flight()
        score = score_flight(flight, [flight])
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_morning_departure_scores_higher_than_red_eye(self):
        morning = _make_flight(id="f1", departure_datetime="2026-04-01T08:00:00",
                               price_total=200.0, duration_minutes=200, stops=0)
        red_eye = _make_flight(id="f2", departure_datetime="2026-04-01T02:00:00",
                               price_total=200.0, duration_minutes=200, stops=0)
        all_flights = [morning, red_eye]

        self.assertGreater(
            score_flight(morning, all_flights),
            score_flight(red_eye, all_flights),
        )

    def test_unknown_baggage_is_neutral(self):
        with_bag = _make_flight(id="f1", baggage_carry_on=True,
                                price_total=200.0, duration_minutes=200, stops=0)
        unknown_bag = _make_flight(id="f2", baggage_carry_on=None,
                                   price_total=200.0, duration_minutes=200, stops=0)
        no_bag = _make_flight(id="f3", baggage_carry_on=False,
                              price_total=200.0, duration_minutes=200, stops=0)
        all_flights = [with_bag, unknown_bag, no_bag]

        score_with = score_flight(with_bag, all_flights)
        score_unknown = score_flight(unknown_bag, all_flights)
        score_no = score_flight(no_bag, all_flights)

        self.assertGreater(score_with, score_unknown)
        self.assertGreater(score_unknown, score_no)


# ---------------------------------------------------------------------------
# label_flights tests
# ---------------------------------------------------------------------------

class FlightLabelingTests(TestCase):

    def test_cheapest_label_assigned_to_lowest_price(self):
        scored = [
            _make_scored("f1", price=100.0, duration=300, stops=1, value_score=65.0),
            _make_scored("f2", price=250.0, duration=180, stops=0, value_score=88.0),
        ]
        labeled = label_flights(scored)
        cheapest = next(f for f in labeled if f.flight.id == "f1")
        self.assertIn("Cheapest", cheapest.labels)

    def test_fastest_label_assigned_to_shortest_duration(self):
        scored = [
            _make_scored("f1", price=200.0, duration=120, stops=0, value_score=80.0),
            _make_scored("f2", price=150.0, duration=420, stops=1, value_score=60.0),
        ]
        labeled = label_flights(scored)
        fastest = next(f for f in labeled if f.flight.id == "f1")
        self.assertIn("Fastest", fastest.labels)

    def test_best_value_label_assigned_to_highest_score(self):
        scored = [
            _make_scored("f1", price=180.0, duration=200, stops=0, value_score=92.0),
            _make_scored("f2", price=130.0, duration=480, stops=2, value_score=45.0),
        ]
        labeled = label_flights(scored)
        best = next(f for f in labeled if f.flight.id == "f1")
        self.assertIn("Best Value", best.labels)

    def test_recommended_label_assigned_to_best_value_flight(self):
        scored = [
            _make_scored("f1", price=150.0, duration=200, stops=0, value_score=90.0),
            _make_scored("f2", price=100.0, duration=600, stops=2, value_score=30.0),
        ]
        labeled = label_flights(scored)
        recommended = next(f for f in labeled if f.flight.id == "f1")
        self.assertIn("Recommended", recommended.labels)

    def test_cheapest_only_outlier_does_not_get_recommended(self):
        # Very cheap but terrible (2 stops, 12 hours) — should not be Recommended
        scored = [
            _make_scored("f1", price=50.0, duration=720, stops=2, value_score=20.0),
            _make_scored("f2", price=300.0, duration=180, stops=0, value_score=95.0),
        ]
        labeled = label_flights(scored)
        bad_flight = next(f for f in labeled if f.flight.id == "f1")
        self.assertNotIn("Recommended", bad_flight.labels)

    def test_single_flight_gets_all_primary_labels(self):
        scored = [_make_scored("f1", price=200.0, duration=200, stops=0, value_score=100.0)]
        labeled = label_flights(scored)
        labels = labeled[0].labels
        self.assertIn("Cheapest", labels)
        self.assertIn("Fastest", labels)
        self.assertIn("Best Value", labels)
        self.assertIn("Recommended", labels)

    def test_label_flights_does_not_mutate_input(self):
        original = [_make_scored("f1", price=200.0, duration=200, stops=0, value_score=80.0)]
        original_labels = original[0].labels
        label_flights(original)
        self.assertEqual(original[0].labels, original_labels)

    def test_label_flights_returns_new_list(self):
        scored = [_make_scored("f1", price=200.0, duration=200, stops=0, value_score=80.0)]
        labeled = label_flights(scored)
        self.assertIsNot(labeled, scored)


# ---------------------------------------------------------------------------
# generate_tradeoff_note tests
# ---------------------------------------------------------------------------

class TradeoffNoteTests(TestCase):

    def test_tradeoff_note_mentions_price_difference(self):
        cheapest = _make_flight(
            id="f1", airline="Spirit", flight_number="NK1",
            departure_datetime="2026-04-01T01:00:00",
            duration_minutes=720, stops=2, price_total=80.0, baggage_carry_on=False,
        )
        recommended = _make_flight(
            id="f2", airline="Delta", flight_number="DL1",
            departure_datetime="2026-04-01T08:00:00",
            duration_minutes=210, stops=0, price_total=240.0, baggage_carry_on=True,
        )
        note = generate_tradeoff_note(cheapest, recommended)
        self.assertIsInstance(note, str)
        self.assertGreater(len(note), 0)
        # Should mention the $160 cost difference
        self.assertIn("160", note)

    def test_tradeoff_note_empty_when_same_flight(self):
        flight = _make_flight()
        note = generate_tradeoff_note(flight, flight)
        self.assertEqual(note, "")

    def test_tradeoff_note_mentions_time_saving(self):
        cheapest = _make_flight(id="f1", duration_minutes=600, price_total=100.0, stops=2)
        recommended = _make_flight(id="f2", duration_minutes=200, price_total=250.0, stops=0)
        note = generate_tradeoff_note(cheapest, recommended)
        # Should reference hours or minutes saved
        self.assertTrue(any(word in note.lower() for word in ("hour", "faster", "quicker", "shorter")))


# ---------------------------------------------------------------------------
# FlightQuery tests
# ---------------------------------------------------------------------------

class FlightQueryTests(TestCase):

    def test_flight_query_defaults(self):
        q = FlightQuery(
            origin="JFK",
            destination="MIA",
            departure_date="2026-04-01",
            return_date=None,
        )
        self.assertEqual(q.passengers, 1)
        self.assertIsNone(q.max_price)
        self.assertIsNone(q.max_stops)
        self.assertEqual(q.cabin_class, "economy")

    def test_flight_query_with_overrides(self):
        q = FlightQuery(
            origin="JFK",
            destination="LAX",
            departure_date="2026-05-01",
            return_date="2026-05-08",
            passengers=2,
            max_price=500.0,
            max_stops=1,
            cabin_class="business",
        )
        self.assertEqual(q.passengers, 2)
        self.assertEqual(q.max_price, 500.0)
        self.assertEqual(q.cabin_class, "business")


# ---------------------------------------------------------------------------
# Intent parser tests
# ---------------------------------------------------------------------------

class FlightIntentParserTests(TestCase):

    @patch("flights.intent.OpenAI")
    def test_parses_basic_round_trip_query(self, MockOpenAI):
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "origin": "JFK",
            "destination": "MIA",
            "departure_date": "2026-04-01",
            "return_date": "2026-04-05",
            "passengers": 1,
            "max_price": None,
            "max_stops": None,
            "cabin_class": "economy",
        })
        MockOpenAI.return_value.responses.create.return_value = mock_response

        from .intent import parse_flight_query
        query = parse_flight_query("Flight from NYC to Miami April 1-5")

        self.assertIsNotNone(query)
        self.assertEqual(query.origin, "JFK")
        self.assertEqual(query.destination, "MIA")
        self.assertEqual(query.departure_date, "2026-04-01")
        self.assertEqual(query.return_date, "2026-04-05")
        self.assertEqual(query.passengers, 1)

    @patch("flights.intent.OpenAI")
    def test_extracts_budget_constraint(self, MockOpenAI):
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": "2026-05-01",
            "return_date": None,
            "passengers": 1,
            "max_price": 300.0,
            "max_stops": None,
            "cabin_class": "economy",
        })
        MockOpenAI.return_value.responses.create.return_value = mock_response

        from .intent import parse_flight_query
        query = parse_flight_query("Cheapest one-way JFK to LA under $300")

        self.assertIsNotNone(query)
        self.assertEqual(query.max_price, 300.0)
        self.assertIsNone(query.return_date)

    @patch("flights.intent.OpenAI")
    def test_extracts_stop_preference(self, MockOpenAI):
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "origin": "ORD",
            "destination": "LHR",
            "departure_date": "2026-06-01",
            "return_date": "2026-06-10",
            "passengers": 1,
            "max_price": None,
            "max_stops": 0,
            "cabin_class": "economy",
        })
        MockOpenAI.return_value.responses.create.return_value = mock_response

        from .intent import parse_flight_query
        query = parse_flight_query("Nonstop Chicago to London, June 1-10")

        self.assertIsNotNone(query)
        self.assertEqual(query.max_stops, 0)

    @patch("flights.intent.OpenAI")
    def test_extracts_passenger_count(self, MockOpenAI):
        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "origin": "JFK",
            "destination": "MCO",
            "departure_date": "2026-07-01",
            "return_date": "2026-07-08",
            "passengers": 4,
            "max_price": None,
            "max_stops": None,
            "cabin_class": "economy",
        })
        MockOpenAI.return_value.responses.create.return_value = mock_response

        from .intent import parse_flight_query
        query = parse_flight_query("Flights for 4 people JFK to Orlando July 1-8")

        self.assertIsNotNone(query)
        self.assertEqual(query.passengers, 4)

    def test_returns_none_when_openai_not_configured(self):
        from .intent import parse_flight_query
        with self.settings(OPENAI_API_KEY=None):
            result = parse_flight_query("Flight to Paris")
        self.assertIsNone(result)

    @patch("flights.intent.OpenAI")
    def test_returns_none_on_invalid_json_response(self, MockOpenAI):
        mock_response = MagicMock()
        mock_response.output_text = "Sorry, I cannot process that request."
        MockOpenAI.return_value.responses.create.return_value = mock_response

        from .intent import parse_flight_query
        query = parse_flight_query("asdfghjkl invalid query !!!!")
        self.assertIsNone(query)

    @patch("flights.intent.OpenAI")
    def test_returns_none_on_openai_exception(self, MockOpenAI):
        MockOpenAI.return_value.responses.create.side_effect = Exception("API error")

        from .intent import parse_flight_query
        query = parse_flight_query("NYC to London")
        self.assertIsNone(query)


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

FLIGHT_SESSION_KEY = "flight_search_results"


class FlightSearchViewTests(TestCase):

    def test_search_page_renders(self):
        response = self.client.get(reverse("flights:search"))
        self.assertEqual(response.status_code, 200)

    def test_search_post_requires_query(self):
        response = self.client.post(reverse("flights:search"), {"query": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "enter")

    @patch("flights.views.parse_flight_query", return_value=None)
    def test_search_post_shows_error_when_parse_fails(self, _mock):
        response = self.client.post(
            reverse("flights:search"),
            {"query": "asdfghjkl"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("flights.views.search_flights", return_value=[])
    @patch("flights.views.parse_flight_query")
    def test_search_post_redirects_to_results(self, mock_parse, _mock_search):
        mock_parse.return_value = FlightQuery(
            origin="JFK",
            destination="MIA",
            departure_date="2026-04-01",
            return_date="2026-04-05",
        )
        response = self.client.post(
            reverse("flights:search"),
            {"query": "NYC to Miami April 1-5"},
        )
        self.assertRedirects(response, reverse("flights:results"))

    @patch("flights.views.search_flights")
    @patch("flights.views.parse_flight_query")
    def test_search_stores_results_in_session(self, mock_parse, mock_search):
        mock_parse.return_value = FlightQuery(
            origin="JFK",
            destination="MIA",
            departure_date="2026-04-01",
            return_date=None,
        )
        mock_search.return_value = []
        self.client.post(reverse("flights:search"), {"query": "JFK to Miami"})
        self.assertIn(FLIGHT_SESSION_KEY, self.client.session)


class FlightResultsViewTests(TestCase):

    def test_results_page_without_session_redirects(self):
        response = self.client.get(reverse("flights:results"))
        self.assertRedirects(response, reverse("flights:search"))

    def test_results_page_renders_with_empty_results(self):
        session = self.client.session
        session[FLIGHT_SESSION_KEY] = {
            "query_text": "NYC to Miami",
            "flights": [],
            "spotlight": {},
        }
        session.save()
        response = self.client.get(reverse("flights:results"))
        self.assertEqual(response.status_code, 200)

    def test_results_page_renders_flights(self):
        session = self.client.session
        session[FLIGHT_SESSION_KEY] = {
            "query_text": "NYC to Miami",
            "flights": [
                {
                    "id": "f1",
                    "airline": "Delta",
                    "flight_number": "DL100",
                    "origin": "JFK",
                    "destination": "MIA",
                    "departure_datetime": "2026-04-01T08:00:00",
                    "arrival_datetime": "2026-04-01T11:30:00",
                    "duration_minutes": 210,
                    "stops": 0,
                    "price_total": 189.0,
                    "baggage_carry_on": True,
                    "booking_url": "https://flights.google.com/?q=test",
                    "labels": ["Recommended", "Best Value"],
                    "value_score": 91.0,
                    "tradeoff_note": "",
                    "source": "amadeus",
                }
            ],
            "spotlight": {
                "recommended": "f1",
                "cheapest": "f1",
                "fastest": "f1",
            },
        }
        session.save()
        response = self.client.get(reverse("flights:results"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delta")
        self.assertContains(response, "189")
