import time
import unittest

from py24so.core.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    """Tests for the RateLimiter class."""

    def test_init(self):
        """Test initialization of rate limiter."""
        limiter = RateLimiter(rate=10, period=60)
        self.assertEqual(limiter.rate, 10)
        self.assertEqual(limiter.period, 60)
        self.assertEqual(limiter.tokens, 10)
        self.assertLessEqual(limiter.last_refill_time, time.time())

    def test_acquire_success(self):
        """Test successful token acquisition."""
        limiter = RateLimiter(rate=5, period=60)
        for _ in range(5):
            success, wait_time = limiter.acquire()
            self.assertTrue(success)
            self.assertIsNone(wait_time)

    def test_acquire_limit_reached(self):
        """Test behavior when limit is reached."""
        limiter = RateLimiter(rate=2, period=10)
        
        # Use all tokens
        success1, wait_time1 = limiter.acquire()
        success2, wait_time2 = limiter.acquire()
        self.assertTrue(success1)
        self.assertTrue(success2)
        self.assertIsNone(wait_time1)
        self.assertIsNone(wait_time2)
        
        # Try to acquire another token (should fail)
        success3, wait_time3 = limiter.acquire(block=False)
        self.assertFalse(success3)
        self.assertIsNone(wait_time3)
        
        # With blocking behavior (should calculate wait time)
        success4, wait_time4 = limiter.acquire(block=True)
        self.assertFalse(success4)
        self.assertIsNotNone(wait_time4)
        self.assertGreater(wait_time4, 0)

    def test_token_refill(self):
        """Test token refill mechanism."""
        # Create a rate limiter with 2 tokens per 1 second
        limiter = RateLimiter(rate=2, period=1)
        
        # Use all tokens
        limiter.acquire()
        limiter.acquire()
        success, _ = limiter.acquire(block=False)
        self.assertFalse(success)
        
        # Wait for token refill (slightly over 1 second to ensure refill)
        time.sleep(1.1)
        
        # Now we should have 2 tokens again
        limiter._refill_tokens()
        self.assertAlmostEqual(limiter.tokens, 2, delta=0.1)
        
        # Try acquiring a token again (should succeed)
        success, wait_time = limiter.acquire()
        self.assertTrue(success)
        self.assertIsNone(wait_time)

    def test_get_status(self):
        """Test getting rate limiter status."""
        limiter = RateLimiter(rate=10, period=60)
        
        # Use some tokens
        limiter.acquire()
        limiter.acquire()
        
        status = limiter.get_status()
        self.assertIn('available_tokens', status)
        self.assertIn('max_rate', status)
        self.assertIn('period_seconds', status)
        
        self.assertAlmostEqual(status['available_tokens'], 8, delta=0.1)
        self.assertEqual(status['max_rate'], 10)
        self.assertEqual(status['period_seconds'], 60)


if __name__ == '__main__':
    unittest.main() 