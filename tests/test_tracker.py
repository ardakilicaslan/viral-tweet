import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import os
import main
import notifier

TWEET = dict(display_name='Örnek', handle='@ornek', likes=25000, retweets=2000, text='&' * 310, link='https://x.com/ornek/status/123')

class TrackerTests(unittest.TestCase):
    def test_bounded_queries_and_drafts(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = os.getcwd()
            try:
                os.chdir(folder)
                with patch.object(main, 'get_top_tweet', return_value=TWEET) as search, patch.object(main, 'send_telegram_message') as send:
                    report = main.run_tracker(target_date='2026-10-31', notify=False)
                    self.assertEqual(report['date'], '2026-10-31')
                    self.assertEqual(search.call_count, 2)
                    for call in search.call_args_list:
                        self.assertIn('since:2026-10-31 until:2026-11-01', call.args[0])
                    send.assert_not_called()
                    self.assertIn('@xzirvesi', Path('reports/2026-10-31-x.txt').read_text(encoding='utf-8'))
            finally:
                os.chdir(previous)

    def test_scrape_failure_propagates(self):
        with patch.object(main, 'get_top_tweet', side_effect=RuntimeError('session')):
            with self.assertRaises(RuntimeError):
                main.run_tracker(target_date='2026-10-31', notify=False)

    def test_html_and_report_date(self):
        with patch.object(notifier.requests, 'post') as post:
            post.return_value.status_code = 200
            self.assertTrue(notifier.send_telegram_message('fake', 'fake', TWEET, report_date='2026-10-31'))
            message = post.call_args.kwargs['json']['text']
            self.assertIn('31.10.2026', message)
            self.assertIn('&amp;' * 297 + '...', message)

if __name__ == '__main__':
    unittest.main()
